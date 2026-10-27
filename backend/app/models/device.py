import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class AudioDevice(Base):
    __tablename__ = "audio_devices"

    id = Column(String(50), primary_key=True)
    model_name = Column(String(100), nullable=False)   # e.g., Shure Axient Digital AD4Q
    channel_name = Column(String(100), nullable=False) # e.g., Lead Vocal (Wireless Handheld)
    frequency_mhz = Column(Float, default=518.250)      # UHF frequency in MHz
    ip_address = Column(String(50), default="192.168.1.101")
    dante_channel = Column(Integer, default=1)
    status = Column(String(20), default="OPTIMAL")     # OPTIMAL, WARNING, CRITICAL, MUTED
    pad_db = Column(Integer, default=0)                # 0 dB or -12 dB
    is_muted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    telemetry = relationship("TelemetrySnapshot", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("SystemAlert", back_populates="device", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "model_name": self.model_name,
            "channel_name": self.channel_name,
            "frequency_mhz": round(self.frequency_mhz, 3),
            "ip_address": self.ip_address,
            "dante_channel": self.dante_channel,
            "status": self.status,
            "pad_db": self.pad_db,
            "is_muted": self.is_muted,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class TelemetrySnapshot(Base):
    __tablename__ = "telemetry_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(50), ForeignKey("audio_devices.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # RF Wireless Metrics
    rssi_dbm = Column(Float, nullable=False)           # -90 dBm (weak) to -30 dBm (strong)
    snr_db = Column(Float, nullable=False)             # Signal-to-Noise Ratio (dB)
    
    # Audio DSP Metrics
    audio_level_dbfs = Column(Float, nullable=False)   # -60 dBFS to 0 dBFS (clip)
    is_clipping = Column(Boolean, default=False)
    
    # Battery & Health
    battery_percentage = Column(Integer, default=100)
    battery_runtime_min = Column(Integer, default=480)
    
    # Network (Dante / AES67 AoIP)
    packet_loss_rate = Column(Float, default=0.0)      # Percentage 0.0 - 100.0
    network_jitter_ms = Column(Float, default=0.2)     # Milliseconds
    
    # Live Synthetic Frequency Spectrum Bins (16 FFT band magnitudes)
    spectrum_bins = Column(JSON, default=list)

    device = relationship("AudioDevice", back_populates="telemetry")

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "rssi_dbm": round(self.rssi_dbm, 1),
            "snr_db": round(self.snr_db, 1),
            "audio_level_dbfs": round(self.audio_level_dbfs, 1),
            "is_clipping": self.is_clipping,
            "battery_percentage": self.battery_percentage,
            "battery_runtime_min": self.battery_runtime_min,
            "packet_loss_rate": round(self.packet_loss_rate, 3),
            "network_jitter_ms": round(self.network_jitter_ms, 2),
            "spectrum_bins": self.spectrum_bins or []
        }

class SystemAlert(Base):
    __tablename__ = "system_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(50), ForeignKey("audio_devices.id"), nullable=False)
    severity = Column(String(20), default="WARNING")   # INFO, WARNING, CRITICAL
    category = Column(String(50), nullable=False)      # RF_INTERFERENCE, AUDIO_CLIPPING, BATTERY_LOW, NETWORK_JITTER
    message = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    device = relationship("AudioDevice", back_populates="alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "suggested_action": self.suggested_action,
            "resolved": self.resolved,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(50), nullable=False)
    trigger_reason = Column(String(100), nullable=False)
    root_cause_analysis = Column(Text, nullable=False)
    remediation_plan = Column(Text, nullable=False)
    recommended_frequency_mhz = Column(Float, nullable=True)
    recommended_pad_db = Column(Integer, nullable=True)
    diagnostic_confidence = Column(Float, default=0.98) # Calibrated rule match confidence
    
    # Verification & Recovery
    applied = Column(Boolean, default=False)
    verification_status = Column(String(20), default="PENDING") # PENDING, VERIFIED, FAILED
    measured_before = Column(JSON, default=dict)
    measured_after = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "trigger_reason": self.trigger_reason,
            "root_cause_analysis": self.root_cause_analysis,
            "remediation_plan": self.remediation_plan,
            "recommended_frequency_mhz": self.recommended_frequency_mhz,
            "recommended_pad_db": self.recommended_pad_db,
            "diagnostic_confidence": self.diagnostic_confidence,
            "ai_confidence": self.diagnostic_confidence,
            "applied": self.applied,
            "verification_status": self.verification_status,
            "measured_before": self.measured_before or {},
            "measured_after": self.measured_after or {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
