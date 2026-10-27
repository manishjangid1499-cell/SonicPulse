import math
import random
import time
from typing import Dict, Any, List

class AudioDeviceSimulator:
    def __init__(self):
        # Device state cache
        self.device_states = {
            "shure-axient-ch1": {
                "active_anomaly": None,
                "pad_db": 0,
                "frequency_mhz": 518.250,
                "base_rssi": -52.0,
                "base_audio_dbfs": -16.0,
                "battery_pct": 92,
                "runtime_min": 440
            },
            "shure-axient-ch2": {
                "active_anomaly": None,
                "pad_db": 0,
                "frequency_mhz": 522.400,
                "base_rssi": -56.0,
                "base_audio_dbfs": -22.0,
                "battery_pct": 78,
                "runtime_min": 370
            },
            "shure-mxa920-conf": {
                "active_anomaly": None,
                "pad_db": 0,
                "frequency_mhz": 550.000,
                "base_rssi": -42.0,
                "base_audio_dbfs": -18.0,
                "battery_pct": 100, # PoE Powered
                "runtime_min": 999
            },
            "shure-slxd-podium": {
                "active_anomaly": None,
                "pad_db": 0,
                "frequency_mhz": 536.800,
                "base_rssi": -65.0,
                "base_audio_dbfs": -20.0,
                "battery_pct": 45,
                "runtime_min": 210
            }
        }

    def trigger_anomaly(self, device_id: str, anomaly_type: str):
        if device_id in self.device_states:
            self.device_states[device_id]["active_anomaly"] = anomaly_type

    def clear_anomaly(self, device_id: str):
        if device_id in self.device_states:
            self.device_states[device_id]["active_anomaly"] = None

    def apply_remediation(self, device_id: str, frequency_mhz: float = None, pad_db: int = None):
        if device_id in self.device_states:
            if frequency_mhz is not None:
                self.device_states[device_id]["frequency_mhz"] = frequency_mhz
                # If was RF collapse, switching frequency fixes it
                if self.device_states[device_id]["active_anomaly"] == "RF_COLLAPSE":
                    self.device_states[device_id]["active_anomaly"] = None

            if pad_db is not None:
                self.device_states[device_id]["pad_db"] = pad_db
                # If was preamp clipping, engaging pad fixes it
                if pad_db == -12 and self.device_states[device_id]["active_anomaly"] == "PREAMP_CLIPPING":
                    self.device_states[device_id]["active_anomaly"] = None

    def generate_snapshot(self, device_id: str) -> Dict[str, Any]:
        state = self.device_states.get(device_id, {
            "active_anomaly": None,
            "pad_db": 0,
            "frequency_mhz": 518.250,
            "base_rssi": -55.0,
            "base_audio_dbfs": -18.0,
            "battery_pct": 85,
            "runtime_min": 400
        })

        anomaly = state.get("active_anomaly")
        t = time.time()

        # 1. RF Metrics Calculation
        if anomaly == "RF_COLLAPSE":
            # Severe RF fade / interference
            rssi = -86.0 + random.uniform(-3.0, 2.0)
            snr = max(4.0, 12.0 + random.uniform(-4.0, 2.0))
        else:
            rssi = state["base_rssi"] + math.sin(t * 0.5) * 2.5 + random.uniform(-1.0, 1.0)
            snr = 28.0 + random.uniform(-1.5, 1.5)

        # 2. Audio DSP Metrics
        pad_offset = state.get("pad_db", 0) # 0 or -12
        if anomaly == "PREAMP_CLIPPING":
            # Excessive acoustic SPL overloading ADC
            raw_audio = 1.5 + random.uniform(0.0, 1.0) # > 0 dBFS
            audio_dbfs = min(0.0, raw_audio + pad_offset)
            is_clipping = audio_dbfs >= -0.1
        else:
            raw_audio = state["base_audio_dbfs"] + math.sin(t * 2.0) * 8.0 + random.uniform(-2.0, 2.0)
            audio_dbfs = max(-60.0, min(0.0, raw_audio + pad_offset))
            is_clipping = False

        # 3. Dante AoIP Network Metrics
        if anomaly == "DANTE_JITTER":
            packet_loss = 4.2 + random.uniform(-0.5, 1.2)
            jitter_ms = 5.4 + random.uniform(-0.8, 1.5)
        else:
            packet_loss = max(0.0, random.uniform(0.0, 0.05))
            jitter_ms = 0.25 + random.uniform(-0.05, 0.15)

        # 4. Generate 16 FFT Spectrum Bins (values between 0.05 and 0.95 for canvas render)
        spectrum = []
        for i in range(16):
            base_mag = 0.2 + 0.5 * math.sin(t * 3.0 + i * 0.4) ** 2
            if anomaly == "PREAMP_CLIPPING":
                # Harmonics saturate upper bins
                base_mag = min(1.0, base_mag * 1.5 + 0.3)
            spectrum.append(round(max(0.05, min(0.98, base_mag + random.uniform(-0.05, 0.05))), 2))

        return {
            "device_id": device_id,
            "rssi_dbm": round(rssi, 1),
            "snr_db": round(snr, 1),
            "audio_level_dbfs": round(audio_dbfs, 1),
            "is_clipping": is_clipping,
            "battery_percentage": state["battery_pct"],
            "battery_runtime_min": state["runtime_min"],
            "packet_loss_rate": round(packet_loss, 3),
            "network_jitter_ms": round(jitter_ms, 2),
            "spectrum_bins": spectrum,
            "frequency_mhz": state["frequency_mhz"],
            "pad_db": state["pad_db"]
        }

device_simulator = AudioDeviceSimulator()
