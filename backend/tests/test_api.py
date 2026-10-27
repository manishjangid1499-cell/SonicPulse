import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import Base, engine, SessionLocal, seed_default_devices
from backend.app.services.simulator import AudioDeviceSimulator
from backend.app.services.diagnostics import AIDiagnosticEngine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    seed_default_devices()
    yield
    Base.metadata.drop_all(bind=engine)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_get_devices():
    res = client.get("/api/devices")
    assert res.status_code == 200
    devices = res.json()
    assert len(devices) >= 4
    models = [d["model_name"] for d in devices]
    assert "Shure Axient Digital AD4Q" in models

def test_device_simulator_physics():
    sim = AudioDeviceSimulator()
    snapshot = sim.generate_snapshot("shure-axient-ch1")
    assert "rssi_dbm" in snapshot
    assert "audio_level_dbfs" in snapshot
    assert len(snapshot["spectrum_bins"]) == 16
    assert snapshot["rssi_dbm"] < 0 # Negative dBm

def test_ai_diagnostic_rf_collapse_and_remediation():
    db = SessionLocal()
    sim = AudioDeviceSimulator()
    engine = AIDiagnosticEngine()

    # Trigger RF collapse
    sim.trigger_anomaly("shure-axient-ch1", "RF_COLLAPSE")
    snapshot = sim.generate_snapshot("shure-axient-ch1")
    assert snapshot["rssi_dbm"] < -80.0

    # Engine should diagnose and produce report
    report = engine.analyze_snapshot(db, snapshot)
    assert report is not None
    assert report.trigger_reason == "RF_INTERFERENCE"
    assert report.recommended_frequency_mhz == 548.750

    # Apply remediation
    remediated = engine.apply_remediation(db, report.id)
    assert remediated.applied == True
    db.close()

def test_ai_diagnostic_preamp_clipping():
    db = SessionLocal()
    sim = AudioDeviceSimulator()
    engine = AIDiagnosticEngine()

    # Trigger clipping
    sim.trigger_anomaly("shure-axient-ch1", "PREAMP_CLIPPING")
    snapshot = sim.generate_snapshot("shure-axient-ch1")
    assert snapshot["is_clipping"] == True or snapshot["audio_level_dbfs"] >= -0.2

    report = engine.analyze_snapshot(db, snapshot)
    assert report is not None
    assert report.trigger_reason == "AUDIO_CLIPPING"
    assert report.recommended_pad_db == -12
    db.close()
