import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import Base, engine, SessionLocal, seed_default_devices
from backend.app.core.config import settings
from backend.app.services.simulator import device_simulator, AudioDeviceSimulator
from backend.app.services.diagnostics import ai_diagnostics, AIDiagnosticEngine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
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
    assert snapshot["rssi_dbm"] < 0  # Negative dBm

def test_ai_diagnostic_rf_collapse_and_verified_remediation():
    db = SessionLocal()
    sim = AudioDeviceSimulator()
    diag_engine = AIDiagnosticEngine()

    # Trigger RF collapse
    sim.trigger_anomaly("shure-axient-ch1", "RF_COLLAPSE")
    snapshot = sim.generate_snapshot("shure-axient-ch1")
    assert snapshot["rssi_dbm"] < settings.RF_RSSI_CRITICAL_DBM

    # Engine diagnoses and produces report with verification_status='PENDING'
    report = diag_engine.analyze_snapshot(db, snapshot)
    assert report is not None
    assert report.trigger_reason == "RF_INTERFERENCE"
    assert report.recommended_frequency_mhz == 548.750
    assert report.verification_status == "PENDING"
    assert report.diagnostic_confidence >= 0.90

    # Apply remediation and verify post-remediation verification works
    remediated = diag_engine.apply_remediation(db, report.id)
    assert remediated.applied is True
    assert remediated.verification_status == "VERIFIED"
    assert remediated.measured_after is not None
    assert remediated.measured_after["rssi_dbm"] >= settings.RF_RSSI_CRITICAL_DBM
    db.close()

def test_ai_diagnostic_preamp_clipping():
    db = SessionLocal()
    sim = AudioDeviceSimulator()
    diag_engine = AIDiagnosticEngine()

    # Trigger clipping
    sim.trigger_anomaly("shure-axient-ch1", "PREAMP_CLIPPING")
    snapshot = sim.generate_snapshot("shure-axient-ch1")
    assert snapshot["is_clipping"] is True or snapshot["audio_level_dbfs"] >= settings.AUDIO_CLIP_THRESHOLD_DBFS

    report = diag_engine.analyze_snapshot(db, snapshot)
    assert report is not None
    assert report.trigger_reason == "AUDIO_CLIPPING"
    assert report.recommended_pad_db == -12
    assert report.verification_status == "PENDING"

    # Apply remediation
    remediated = diag_engine.apply_remediation(db, report.id)
    assert remediated.applied is True
    assert remediated.verification_status == "VERIFIED"
    db.close()

def test_ai_diagnostic_dante_jitter():
    """Verify P0 fix: Dante jitter threshold at 2.0 ms generates alert and diagnostic report."""
    db = SessionLocal()
    sim = AudioDeviceSimulator()
    diag_engine = AIDiagnosticEngine()

    # Trigger jitter anomaly
    sim.trigger_anomaly("shure-mxa920-conf", "DANTE_JITTER")
    snapshot = sim.generate_snapshot("shure-mxa920-conf")
    assert snapshot["network_jitter_ms"] > settings.DANTE_JITTER_THRESHOLD_MS

    # Engine diagnoses and produces report
    report = diag_engine.analyze_snapshot(db, snapshot)
    assert report is not None
    assert report.trigger_reason == "NETWORK_JITTER"
    assert report.verification_status == "PENDING"
    assert report.diagnostic_confidence >= 0.90
    db.close()

def test_alert_deduplication():
    """Verify P1 fix: rapid repeated fault frames are suppressed within cooldown."""
    db = SessionLocal()
    sim = AudioDeviceSimulator()
    diag_engine = AIDiagnosticEngine()

    sim.trigger_anomaly("shure-axient-ch1", "PREAMP_CLIPPING")
    snapshot = sim.generate_snapshot("shure-axient-ch1")

    # First analysis creates report
    report1 = diag_engine.analyze_snapshot(db, snapshot)
    assert report1 is not None

    # Immediate second analysis should be suppressed by deduplication cooldown
    report2 = diag_engine.analyze_snapshot(db, snapshot)
    assert report2 is None
    db.close()

def test_api_unknown_device_404():
    """Verify P1 fix: API returns 404 for unknown device IDs."""
    res = client.get("/api/devices/non-existent-device-id")
    assert res.status_code == 404

    res = client.post("/api/devices/non-existent-device-id/simulate", json={"anomaly_type": "RF_COLLAPSE"})
    assert res.status_code == 404

def test_api_schema_validation_422():
    """Verify P1 fix: invalid frequency or pad rejects with 422 Unprocessable Entity."""
    # Out of UHF range (frequency > 698.0 MHz)
    res = client.post("/api/devices/shure-axient-ch1/action", json={"frequency_mhz": 999.0})
    assert res.status_code == 422

    # Invalid pad (only 0 or -12 is valid)
    res = client.post("/api/devices/shure-axient-ch1/action", json={"pad_db": -6})
    assert res.status_code == 422

    # Invalid anomaly type
    res = client.post("/api/devices/shure-axient-ch1/simulate", json={"anomaly_type": "INVALID_ANOMALY"})
    assert res.status_code == 422

def test_api_full_remediation_cycle():
    """Test full API cycle: simulate anomaly -> view diagnostic -> apply remediation."""
    # 1. Trigger RF collapse via API
    sim_res = client.post("/api/devices/shure-axient-ch1/simulate", json={"anomaly_type": "RF_COLLAPSE"})
    assert sim_res.status_code == 200
    report_data = sim_res.json()["diagnostic_report_created"]
    assert report_data is not None
    report_id = report_data["id"]

    # 2. Apply remediation via API
    apply_res = client.post(f"/api/diagnostics/{report_id}/apply")
    assert apply_res.status_code == 200
    applied_data = apply_res.json()
    assert applied_data["applied"] is True
    assert applied_data["verification_status"] == "VERIFIED"
    assert applied_data["measured_after"] is not None

    # 3. Check device status returned to OPTIMAL
    dev_res = client.get("/api/devices/shure-axient-ch1")
    assert dev_res.status_code == 200
    assert dev_res.json()["status"] == "OPTIMAL"
