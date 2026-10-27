from typing import Optional, List
from pydantic import BaseModel

class DeviceActionRequest(BaseModel):
    pad_db: Optional[int] = None
    frequency_mhz: Optional[float] = None
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
    ai_confidence: float
    applied: bool
    created_at: Optional[str]

class TriggerAnomalyRequest(BaseModel):
    anomaly_type: str # RF_COLLAPSE, PREAMP_CLIPPING, DANTE_JITTER
