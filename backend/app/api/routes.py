import asyncio
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db, SessionLocal
from backend.app.models.device import AudioDevice, SystemAlert, DiagnosticReport, TelemetrySnapshot
from backend.app.schemas.device import (
    DeviceResponse,
    DeviceActionRequest,
    AlertResponse,
    DiagnosticResponse,
    TriggerAnomalyRequest,
    TelemetryResponse
)
from backend.app.services.simulator import device_simulator
from backend.app.services.diagnostics import ai_diagnostics

router = APIRouter()

@router.get("/devices", response_model=List[DeviceResponse])
def get_devices(db: Session = Depends(get_db)):
    devices = db.query(AudioDevice).all()
    return [d.to_dict() for d in devices]

@router.get("/devices/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(AudioDevice).filter(AudioDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Audio device '{device_id}' not found")
    return device.to_dict()

@router.post("/devices/{device_id}/action", response_model=DeviceResponse)
def update_device_action(device_id: str, action: DeviceActionRequest, db: Session = Depends(get_db)):
    device = db.query(AudioDevice).filter(AudioDevice.id == device_id).first()
    if not device or not device_simulator.has_device(device_id):
        raise HTTPException(status_code=404, detail=f"Audio device '{device_id}' not found")

    if action.pad_db is not None:
        device.pad_db = action.pad_db
        device_simulator.apply_remediation(device_id, pad_db=action.pad_db)

    if action.frequency_mhz is not None:
        device.frequency_mhz = action.frequency_mhz
        device_simulator.apply_remediation(device_id, frequency_mhz=action.frequency_mhz)

    if action.is_muted is not None:
        device.is_muted = action.is_muted

    db.commit()
    db.refresh(device)
    return device.to_dict()

@router.post("/devices/{device_id}/simulate")
def trigger_device_simulation(device_id: str, req: TriggerAnomalyRequest, db: Session = Depends(get_db)):
    device = db.query(AudioDevice).filter(AudioDevice.id == device_id).first()
    if not device or not device_simulator.has_device(device_id):
        raise HTTPException(status_code=404, detail=f"Audio device '{device_id}' not found")

    device_simulator.trigger_anomaly(device_id, req.anomaly_type.value)
    
    # Run instantaneous diagnostic check
    snapshot = device_simulator.generate_snapshot(device_id)
    report = ai_diagnostics.analyze_snapshot(db, snapshot)

    return {
        "status": "anomaly_triggered",
        "device_id": device_id,
        "anomaly": req.anomaly_type.value,
        "diagnostic_report_created": report.to_dict() if report else None
    }

@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(SystemAlert).order_by(SystemAlert.created_at.desc()).limit(20).all()
    return [a.to_dict() for a in alerts]

@router.get("/diagnostics", response_model=List[DiagnosticResponse])
def get_diagnostics(db: Session = Depends(get_db)):
    reports = db.query(DiagnosticReport).order_by(DiagnosticReport.created_at.desc()).limit(10).all()
    return [r.to_dict() for r in reports]

@router.post("/diagnostics/{report_id}/apply", response_model=DiagnosticResponse)
def apply_diagnostic_remediation(report_id: str, db: Session = Depends(get_db)):
    report = ai_diagnostics.apply_remediation(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Diagnostic report not found")
    return report.to_dict()

@router.get("/telemetry/live")
def get_live_telemetry():
    device_ids = list(device_simulator.devices.keys())
    return [device_simulator.generate_snapshot(did) for did in device_ids]

# Real-time streaming WebSocket
@router.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    device_ids = list(device_simulator.devices.keys())
    interval_sec = settings.TELEMETRY_INTERVAL_MS / 1000.0
    try:
        while True:
            db = SessionLocal()
            try:
                snapshots = []
                for did in device_ids:
                    s = device_simulator.generate_snapshot(did)
                    # Check for anomalies on the fly (with alert deduplication cooldown)
                    ai_diagnostics.analyze_snapshot(db, s)
                    snapshots.append(s)

                await websocket.send_text(json.dumps({
                    "timestamp": asyncio.get_event_loop().time(),
                    "devices": snapshots
                }))
            finally:
                db.close()
            await asyncio.sleep(interval_sec)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
