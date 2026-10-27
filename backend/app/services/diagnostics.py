import time
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.device import SystemAlert, DiagnosticReport, AudioDevice
from backend.app.services.simulator import device_simulator

class AIDiagnosticEngine:
    def __init__(self):
        # Alert cooldown tracking: (device_id, category) -> timestamp
        self._recent_alerts: Dict[tuple, float] = {}

    def _should_suppress_alert(self, device_id: str, category: str) -> bool:
        now = time.time()
        key = (device_id, category)
        last_time = self._recent_alerts.get(key, 0.0)
        if (now - last_time) < settings.ALERT_DEDUPLICATION_COOLDOWN_SEC:
            return True
        self._recent_alerts[key] = now
        return False

    def clear_cooldown(self, device_id: str, category: Optional[str] = None):
        if category:
            self._recent_alerts.pop((device_id, category), None)
        else:
            keys_to_remove = [k for k in self._recent_alerts if k[0] == device_id]
            for k in keys_to_remove:
                self._recent_alerts.pop(k, None)

    def analyze_snapshot(self, db: Session, snapshot: Dict[str, Any]) -> Optional[DiagnosticReport]:
        device_id = snapshot["device_id"]
        rssi = snapshot["rssi_dbm"]
        snr = snapshot["snr_db"]
        audio_level = snapshot["audio_level_dbfs"]
        is_clipping = snapshot["is_clipping"]
        jitter = snapshot["network_jitter_ms"]

        # 1. RF Carrier Interference / Multipath Collapse
        if rssi < settings.RF_RSSI_CRITICAL_DBM or snr < settings.RF_SNR_CRITICAL_DB:
            if self._should_suppress_alert(device_id, "RF_INTERFERENCE"):
                return None

            rec_freq = 548.750 # Intermodulation-free UHF coordinated backup frequency
            alert = SystemAlert(
                device_id=device_id,
                severity="CRITICAL",
                category="RF_INTERFERENCE",
                message=f"RF carrier degradation: RSSI at {rssi} dBm (threshold: {settings.RF_RSSI_CRITICAL_DBM} dBm), SNR at {snr} dB.",
                suggested_action=f"Re-tune wireless receiver to intermod-free coordinated channel {rec_freq} MHz."
            )
            db.add(alert)

            report = DiagnosticReport(
                device_id=device_id,
                trigger_reason="RF_INTERFERENCE",
                root_cause_analysis=(
                    f"Carrier frequency experienced external RF intermodulation or multipath phase cancellation. "
                    f"Measured RSSI dropped to {rssi} dBm (< {settings.RF_RSSI_CRITICAL_DBM} dBm) and SNR dropped to {snr} dB (< {settings.RF_SNR_CRITICAL_DB} dB). "
                    f"High probability of digital mute/dropouts."
                ),
                remediation_plan=f"Re-tune receiver to verified intermodulation-free UHF backup channel {rec_freq} MHz.",
                recommended_frequency_mhz=rec_freq,
                recommended_pad_db=None,
                diagnostic_confidence=0.98,
                verification_status="PENDING",
                measured_before=snapshot
            )
            db.add(report)

            dev = db.query(AudioDevice).filter(AudioDevice.id == device_id).first()
            if dev:
                dev.status = "CRITICAL"

            db.commit()
            db.refresh(report)
            return report

        # 2. Audio Preamplifier ADC Clipping Overload
        elif is_clipping or audio_level >= settings.AUDIO_CLIP_THRESHOLD_DBFS:
            if self._should_suppress_alert(device_id, "AUDIO_CLIPPING"):
                return None

            alert = SystemAlert(
                device_id=device_id,
                severity="WARNING",
                category="AUDIO_CLIPPING",
                message=f"Preamplifier ADC clipping detected at {audio_level} dBFS (threshold: {settings.AUDIO_CLIP_THRESHOLD_DBFS} dBFS).",
                suggested_action="Engage internal -12 dB hardware pad to preserve analog dynamic range."
            )
            db.add(alert)

            report = DiagnosticReport(
                device_id=device_id,
                trigger_reason="AUDIO_CLIPPING",
                root_cause_analysis=(
                    f"Acoustic Sound Pressure Level (SPL) overloaded input preamplifier stage. "
                    f"ADC reached full scale ({audio_level} dBFS), producing square-wave harmonic distortion."
                ),
                remediation_plan="Engage internal -12 dB analog attenuator pad in the DSP chain.",
                recommended_frequency_mhz=None,
                recommended_pad_db=-12,
                diagnostic_confidence=0.99,
                verification_status="PENDING",
                measured_before=snapshot
            )
            db.add(report)

            dev = db.query(AudioDevice).filter(AudioDevice.id == device_id).first()
            if dev:
                dev.status = "WARNING"

            db.commit()
            db.refresh(report)
            return report

        # 3. Dante AoIP Precision Time Protocol (PTP v2) Jitter
        elif jitter > settings.DANTE_JITTER_THRESHOLD_MS:
            if self._should_suppress_alert(device_id, "NETWORK_JITTER"):
                return None

            alert = SystemAlert(
                device_id=device_id,
                severity="WARNING",
                category="NETWORK_JITTER",
                message=f"Dante AoIP jitter exceeded tolerance ({jitter} ms > {settings.DANTE_JITTER_THRESHOLD_MS} ms threshold).",
                suggested_action="Verify switch PTP v2 QoS priority queues or switch to secondary Dante redundancy port."
            )
            db.add(alert)

            # P0 FIX: Jitter now generates a complete DiagnosticReport!
            report = DiagnosticReport(
                device_id=device_id,
                trigger_reason="NETWORK_JITTER",
                root_cause_analysis=(
                    f"Dante AoIP network latency jitter measured at {jitter} ms, exceeding IEEE 1588 PTP v2 sync threshold ({settings.DANTE_JITTER_THRESHOLD_MS} ms). "
                    f"Risk of audio buffer under-runs and click artifacts."
                ),
                remediation_plan="Inspect network switch QoS DiffServ configuration (DSCP EF/46) and verify secondary Dante Gigabit link.",
                recommended_frequency_mhz=None,
                recommended_pad_db=None,
                diagnostic_confidence=0.95,
                verification_status="PENDING",
                measured_before=snapshot
            )
            db.add(report)

            dev = db.query(AudioDevice).filter(AudioDevice.id == device_id).first()
            if dev and dev.status == "OPTIMAL":
                dev.status = "WARNING"

            db.commit()
            db.refresh(report)
            return report

        return None

    def apply_remediation(self, db: Session, report_id: str) -> Optional[DiagnosticReport]:
        """
        P0 FIX: Apply remediation, take fresh telemetry snapshot, and verify recovery
        before marking device healthy!
        """
        report = db.query(DiagnosticReport).filter(DiagnosticReport.id == report_id).first()
        if not report:
            return None

        device_id = report.device_id
        dev = db.query(AudioDevice).filter(AudioDevice.id == device_id).first()

        # 1. Apply hardware / simulator changes
        if report.recommended_frequency_mhz:
            if dev:
                dev.frequency_mhz = report.recommended_frequency_mhz
            device_simulator.apply_remediation(device_id, frequency_mhz=report.recommended_frequency_mhz)

        if report.recommended_pad_db is not None:
            if dev:
                dev.pad_db = report.recommended_pad_db
            device_simulator.apply_remediation(device_id, pad_db=report.recommended_pad_db)

        # 2. Take fresh post-remediation snapshot to verify fault has cleared!
        fresh_snapshot = device_simulator.generate_snapshot(device_id)
        report.measured_after = fresh_snapshot

        # 3. Verify recovery against thresholds
        is_recovered = True
        if report.trigger_reason == "RF_INTERFERENCE":
            if fresh_snapshot["rssi_dbm"] < settings.RF_RSSI_CRITICAL_DBM or fresh_snapshot["snr_db"] < settings.RF_SNR_CRITICAL_DB:
                is_recovered = False
        elif report.trigger_reason == "AUDIO_CLIPPING":
            if fresh_snapshot["is_clipping"] or fresh_snapshot["audio_level_dbfs"] >= settings.AUDIO_CLIP_THRESHOLD_DBFS:
                is_recovered = False
        elif report.trigger_reason == "NETWORK_JITTER":
            if fresh_snapshot["network_jitter_ms"] > settings.DANTE_JITTER_THRESHOLD_MS:
                is_recovered = False

        if is_recovered:
            if dev:
                dev.status = "OPTIMAL"
            report.verification_status = "VERIFIED"
            self.clear_cooldown(device_id, report.trigger_reason)
        else:
            report.verification_status = "FAILED"

        report.applied = True
        db.commit()
        db.refresh(report)
        return report

ai_diagnostics = AIDiagnosticEngine()
