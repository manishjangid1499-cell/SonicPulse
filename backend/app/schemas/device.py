from enum import Enum
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class AnomalyTypeEnum(str, Enum):
    RF_COLLAPSE = "RF_COLLAPSE"
    PREAMP_CLIPPING = "PREAMP_CLIPPING"
    DANTE_JITTER = "DANTE_JITTER"

class DeviceActionRequest(BaseModel):
    pad_db: Optional[Literal[0, -12]] = Field(None, description="Attenuation pad in dB (0 or -12)")
    frequency_mhz: Optional[float] = Field(None, ge=470.0, le=698.0, description="UHF tuning frequency in MHz")
    is_muted: Optional[bool] = None

class DeviceResponse(BaseModel):
    id: str
    model_name: str
    channel_name: str
    frequency_mhz: float
    ip_address: str
    dante_channel: int
    status: str
    pad_db: int
    is_muted: bool
    created_at: Optional[str]

class TelemetryResponse(BaseModel):
    id: str
    device_id: str
    timestamp: Optional[str]
    rssi_dbm: float
    snr_db: float
    audio_level_dbfs: float
    is_clipping: bool
    battery_percentage: int
    battery_runtime_min: int
    packet_loss_rate: float
    network_jitter_ms: float
    spectrum_bins: List[float]

class AlertResponse(BaseModel):
    id: str
    device_id: str
    severity: str
    category: str
    message: str
    suggested_action: str
    resolved: bool
    created_at: Optional[str]

class DiagnosticResponse(BaseModel):
    id: str
    device_id: str
    trigger_reason: str
    root_cause_analysis: str
    remediation_plan: str
    recommended_frequency_mhz: Optional[float]
    recommended_pad_db: Optional[int]
    diagnostic_confidence: float
    ai_confidence: Optional[float] = None
    applied: bool
    verification_status: str
    measured_before: dict
    measured_after: dict
    created_at: Optional[str]

class TriggerAnomalyRequest(BaseModel):
    anomaly_type: AnomalyTypeEnum
