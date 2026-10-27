from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.device import SystemAlert, DiagnosticReport, AudioDevice
from backend.app.services.simulator import device_simulator

class AIDiagnosticEngine:
    def analyze_snapshot(self, db: Session, snapshot: Dict[str, Any]) -> Optional[DiagnosticReport]:
        device_id = snapshot["device_id"]
        rssi = snapshot["rssi_dbm"]
        snr = snapshot["snr_db"]
        audio_level = snapshot["audio_level_dbfs"]
        is_clipping = snapshot["is_clipping"]
        jitter = snapshot["network_jitter_ms"]

        report = None

        # 1. Check for RF Interference / Dropouts
        if rssi < -80.0 or snr < 10.0:
            rec_freq = 548.750
            alert = SystemAlert(
                device_id=device_id,
                severity="CRITICAL",
                category="RF_INTERFERENCE",
                message=f"RF carrier degradation: RSSI at {rssi} dBm, SNR collapsed to {snr} dB.",
                suggested_action=f"Re-tune wireless receiver to coordinated channel {rec_freq} MHz."
            )
            db.add(alert)

            report = DiagnosticReport(
                device_id=device_id,
                trigger_reason="RF_INTERFERENCE",
                root_cause_analysis=(
                    f"Carrier frequency experienced external intermodulation or multipath phase cancellation. "
                    f"RSSI dropped to {rssi} dBm (threshold: -80 dBm) and SNR dropped to {snr} dB. "
                    f"Calculated high risk of audible digital mute."
                ),
                remediation_plan=(
                    f"Execute automated channel scan and retune receiver to intermod-free backup frequency: {rec_freq} MHz."
                ),
                recommended_frequency_mhz=rec_freq,
                recommended_pad_db=None,
                ai_confidence=0.96
            )
            db.add(report)

            # Update device status in DB
            dev = db.query(AudioDevice).filter(AudioDevice.id == device_id).first()
            if dev:
                dev.status = "CRITICAL"

            db.commit()
            return report

        # 2. Check for Preamp Audio Clipping
        elif is_clipping or audio_level >= -0.2:
            alert = SystemAlert(
                device_id=device_id,
                severity="WARNING",
                category="AUDIO_CLIPPING",
                message=f"Preamplifier ADC clipping detected at {audio_level} dBFS.",
                suggested_action="Engage internal -12 dB hardware pad to preserve dynamic range."
            )
            db.add(alert)

            report = DiagnosticReport(
                device_id=device_id,
                trigger_reason="AUDIO_CLIPPING",
                root_cause_analysis=(
                    f"Sound Pressure Level (SPL) exceeded input stage headroom. "
                    f"A/D converter hit full scale (0 dBFS), causing square-wave harmonic distortion."
                ),
                remediation_plan="Engage internal -12 dB analog attenuator pad in the DSP chain.",
                recommended_frequency_mhz=None,
                recommended_pad_db=-12,
                ai_confidence=0.98
            )
            db.add(report)

            dev = db.query(AudioDevice).filter(AudioDevice.id == device_id).first()
            if dev:
                dev.status = "WARNING"

            db.commit()
            return report

        # 3. Check for Dante Network Jitter
        elif jitter > 2.5:
            alert = SystemAlert(
                device_id=device_id,
                severity="WARNING",
                category="NETWORK_JITTER",
                message=f"Dante AoIP jitter exceeded tolerance ({jitter} ms > 2.0 ms threshold).",
                suggested_action="Verify Gigabit switch PTP v2 QoS settings or switch to secondary Dante redundancy port."
            )
            db.add(alert)
            db.commit()

        return None

    def apply_remediation(self, db: Session, report_id: str) -> Optional[DiagnosticReport]:
        report = db.query(DiagnosticReport).filter(DiagnosticReport.id == report_id).first()
        if not report:
            return None

        device_id = report.device_id
        dev = db.query(AudioDevice).filter(AudioDevice.id == device_id).first()

        if report.recommended_frequency_mhz:
            if dev:
                dev.frequency_mhz = report.recommended_frequency_mhz
            device_simulator.apply_remediation(device_id, frequency_mhz=report.recommended_frequency_mhz)

        if report.recommended_pad_db is not None:
            if dev:
                dev.pad_db = report.recommended_pad_db
            device_simulator.apply_remediation(device_id, pad_db=report.recommended_pad_db)

        if dev:
            dev.status = "OPTIMAL"

        report.applied = True
        db.commit()
        db.refresh(report)
        return report

ai_diagnostics = AIDiagnosticEngine()
