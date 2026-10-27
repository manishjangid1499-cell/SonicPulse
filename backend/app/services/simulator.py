import math
import random
import time
from typing import Dict, Any, Optional

class AudioDeviceSimulator:
    def __init__(self):
        # Authoritative device state dictionary for the simulated Shure fleet
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

    def has_device(self, device_id: str) -> bool:
        return device_id in self.device_states

    def trigger_anomaly(self, device_id: str, anomaly_type: str) -> bool:
        if device_id in self.device_states:
            self.device_states[device_id]["active_anomaly"] = anomaly_type
            return True
        return False

    def clear_anomaly(self, device_id: str):
        if device_id in self.device_states:
            self.device_states[device_id]["active_anomaly"] = None

    def apply_remediation(self, device_id: str, frequency_mhz: Optional[float] = None, pad_db: Optional[int] = None) -> bool:
        if device_id not in self.device_states:
            return False

        state = self.device_states[device_id]
        if frequency_mhz is not None:
            state["frequency_mhz"] = frequency_mhz
            # Changing carrier frequency to clear channel resolves RF collapse
            if state["active_anomaly"] == "RF_COLLAPSE":
                state["active_anomaly"] = None

        if pad_db is not None:
            state["pad_db"] = pad_db
            # Engaging -12dB hardware pad attenuates analog preamp and stops clipping
            if pad_db == -12 and state["active_anomaly"] == "PREAMP_CLIPPING":
                state["active_anomaly"] = None

        return True

    def generate_snapshot(self, device_id: str) -> Dict[str, Any]:
        if device_id not in self.device_states:
            raise KeyError(f"Unknown audio device: {device_id}")

        state = self.device_states[device_id]
        anomaly = state.get("active_anomaly")
        t = time.time()

        # 1. RF Wireless Metrics Calculation
        if anomaly == "RF_COLLAPSE":
            # Severe external carrier interference / fading
            rssi = -86.4 + random.uniform(-2.0, 1.5)
            snr = max(4.0, 8.2 + random.uniform(-2.0, 1.5))
        else:
            rssi = state["base_rssi"] + math.sin(t * 0.5) * 2.0 + random.uniform(-0.8, 0.8)
            snr = 28.5 + random.uniform(-1.0, 1.0)

        # 2. Audio DSP Metrics Calculation
        pad_offset = state.get("pad_db", 0) # 0 or -12
        if anomaly == "PREAMP_CLIPPING":
            # Acoustic transient overloading ADC without pad
            raw_audio = 2.0 + random.uniform(0.0, 1.2)
            audio_dbfs = min(0.0, raw_audio + pad_offset)
            is_clipping = audio_dbfs >= -0.1
        else:
            raw_audio = state["base_audio_dbfs"] + math.sin(t * 2.0) * 7.0 + random.uniform(-1.5, 1.5)
            audio_dbfs = max(-60.0, min(0.0, raw_audio + pad_offset))
            is_clipping = False

        # 3. Dante AoIP Network Metrics Calculation
        if anomaly == "DANTE_JITTER":
            packet_loss = 4.2 + random.uniform(-0.4, 0.8)
            jitter_ms = 4.8 + random.uniform(-0.5, 1.0) # Strictly > 2.0 ms threshold
        else:
            packet_loss = max(0.0, random.uniform(0.0, 0.04))
            jitter_ms = 0.25 + random.uniform(-0.04, 0.08)

        # 4. 16 FFT Spectrum Bins (values between 0.05 and 0.98)
        spectrum = []
        for i in range(16):
            base_mag = 0.2 + 0.45 * math.sin(t * 3.0 + i * 0.4) ** 2
            if anomaly == "PREAMP_CLIPPING":
                base_mag = min(1.0, base_mag * 1.4 + 0.25)
            spectrum.append(round(max(0.05, min(0.98, base_mag + random.uniform(-0.04, 0.04))), 2))

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
