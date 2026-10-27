import React, { useState, useEffect, useRef } from "react";
import { 
  Radio, 
  Volume2, 
  Activity, 
  Battery, 
  Cpu, 
  AlertTriangle, 
  CheckCircle2, 
  Sliders, 
  Zap, 
  RefreshCw,
  ShieldAlert,
  Server
} from "lucide-react";
import "./App.css";

const API_BASE = "http://localhost:8000/api";
const WS_BASE = "ws://localhost:8000/api/ws/telemetry";

export default function App() {
  const [devices, setDevices] = useState([]);
  const [telemetry, setTelemetry] = useState({});
  const [selectedDeviceId, setSelectedDeviceId] = useState("shure-axient-ch1");
  const [diagnostics, setDiagnostics] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const canvasRef = useRef(null);

  // 1. Initial Device Fleet & Diagnostics Fetch
  const fetchInitialData = async () => {
    try {
      const [devRes, diagRes, alertRes] = await Promise.all([
        fetch(`${API_BASE}/devices`),
        fetch(`${API_BASE}/diagnostics`),
        fetch(`${API_BASE}/alerts`)
      ]);
      if (devRes.ok) setDevices(await devRes.json());
      if (diagRes.ok) setDiagnostics(await diagRes.json());
      if (alertRes.ok) setAlerts(await alertRes.json());
    } catch (e) {
      console.error("Failed to load initial device fleet:", e);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  // 2. Real-Time WebSocket Telemetry Stream with Fallback
  useEffect(() => {
    let ws = null;
    let fallbackInterval = null;

    const connectWebSocket = () => {
      try {
        ws = new WebSocket(WS_BASE);
        ws.onopen = () => {
          setIsConnected(true);
          if (fallbackInterval) clearInterval(fallbackInterval);
        };
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.devices) {
            const map = {};
            data.devices.forEach((d) => {
              map[d.device_id] = d;
            });
            setTelemetry(map);
          }
        };
        ws.onclose = () => {
          setIsConnected(false);
          // Auto reconnect after 2 seconds
          setTimeout(connectWebSocket, 2000);
        };
        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        console.warn("WebSocket failed, falling back to HTTP polling:", err);
      }
    };

    connectWebSocket();

    // Secondary HTTP poll every 2s for alerts and reports
    const syncInterval = setInterval(async () => {
      try {
        const [diagRes, alertRes, devRes] = await Promise.all([
          fetch(`${API_BASE}/diagnostics`),
          fetch(`${API_BASE}/alerts`),
          fetch(`${API_BASE}/devices`)
        ]);
        if (diagRes.ok) setDiagnostics(await diagRes.json());
        if (alertRes.ok) setAlerts(await alertRes.json());
        if (devRes.ok) setDevices(await devRes.json());
      } catch (e) {}
    }, 2000);

    return () => {
      if (ws) ws.close();
      clearInterval(syncInterval);
    };
  }, []);

  // 3. 60 FPS HTML5 Canvas Real-Time Spectrum & Oscilloscope Waveform
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let animId;
    let phase = 0;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      const activeTelem = telemetry[selectedDeviceId] || {};
      const bins = activeTelem.spectrum_bins || Array(16).fill(0.2);
      const isClip = activeTelem.is_clipping;

      // Draw Spectrum Bars
      const barWidth = width / bins.length;
      bins.forEach((mag, i) => {
        const barHeight = mag * (height - 30);
        const x = i * barWidth;
        const y = height - barHeight;

        // Gradient color: Cyan -> Emerald -> Red on clip
        const grad = ctx.createLinearGradient(0, height, 0, y);
        grad.addColorStop(0, "rgba(14, 165, 233, 0.4)");
        grad.addColorStop(0.7, isClip ? "#ef4444" : "#10b981");
        grad.addColorStop(1, isClip ? "#dc2626" : "#38bdf8");

        ctx.fillStyle = grad;
        ctx.fillRect(x + 2, y, barWidth - 4, barHeight);
      });

      // Draw Oscilloscope Waveform Overlay
      ctx.beginPath();
      ctx.lineWidth = 2;
      ctx.strokeStyle = isClip ? "#ef4444" : "#38bdf8";
      for (let x = 0; x < width; x += 3) {
        const amp = (activeTelem.audio_level_dbfs ? Math.max(5, (activeTelem.audio_level_dbfs + 60) * 0.8) : 20);
        const y = height / 2 + Math.sin(x * 0.03 + phase) * amp;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      phase += 0.15;
      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, [telemetry, selectedDeviceId]);

  // Actions
  const handleSimulate = async (type) => {
    try {
      await fetch(`${API_BASE}/devices/${selectedDeviceId}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ anomaly_type: type })
      });
      fetchInitialData();
    } catch (e) {
      console.error("Simulation failed:", e);
    }
  };

  const handleApplyRemediation = async (reportId) => {
    try {
      const res = await fetch(`${API_BASE}/diagnostics/${reportId}/apply`, {
        method: "POST"
      });
      if (res.ok) {
        fetchInitialData();
      }
    } catch (e) {
      console.error("Remediation error:", e);
    }
  };

  const selectedDevice = devices.find((d) => d.id === selectedDeviceId) || devices[0];
  const activeTelem = telemetry[selectedDeviceId] || {
    rssi_dbm: -52.0,
    snr_db: 28.0,
    audio_level_dbfs: -18.0,
    is_clipping: false,
    battery_percentage: 90,
    battery_runtime_min: 420,
    packet_loss_rate: 0.01,
    network_jitter_ms: 0.3
  };

  return (
    <div className="app-shell">
      {/* Top Header */}
      <header className="app-header">
        <div className="brand-box">
          <div className="brand-badge">SP</div>
          <div>
            <div className="brand-title">SonicPulse</div>
            <div className="brand-sub">Real-Time Networked Audio Device Telemetry &amp; AI Diagnostic Platform</div>
          </div>
        </div>

        <div className="header-status-strip">
          <div className="live-indicator">
            <div className="dot-pulse" style={{ background: isConnected ? "var(--shure-green)" : "var(--warning-amber)" }} />
            <span>{isConnected ? "LIVE TELEMETRY (4 HZ)" : "STREAM RECONNECTING"}</span>
          </div>
          <div style={{ fontSize: "12px", color: "var(--text-sub)" }}>
            Fleet Size: <strong style={{ color: "var(--text-main)" }}>{devices.length} Nodes</strong>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="dashboard-grid">
        {/* Left: Device Fleet Cards & Spectrum */}
        <section className="device-fleet-panel">
          <div className="cards-container">
            {devices.map((dev) => {
              const t = telemetry[dev.id] || {};
              const audioLevel = t.audio_level_dbfs ?? -30;
              const vuPercent = Math.min(100, Math.max(0, ((audioLevel + 60) / 60) * 100));
              const isSelected = dev.id === selectedDeviceId;

              return (
                <div
                  key={dev.id}
                  className={`device-card ${isSelected ? "active" : ""}`}
                  onClick={() => setSelectedDeviceId(dev.id)}
                >
                  <div className="card-top">
                    <div>
                      <div className="device-channel-name">{dev.channel_name}</div>
                      <div className="device-model">{dev.model_name} • Ch {dev.dante_channel}</div>
                    </div>
                    <span className={`status-pill ${dev.status}`}>{dev.status}</span>
                  </div>

                  {/* Meters Row */}
                  <div className="metrics-row">
                    <div className="gauge-box">
                      <span className="gauge-label">RF Signal (RSSI)</span>
                      <span
                        className="gauge-val"
                        style={{ color: (t.rssi_dbm < -80 ? "var(--clip-red)" : "var(--rf-blue)") }}
                      >
                        {t.rssi_dbm ?? -55} dBm
                      </span>
                    </div>

                    <div className="gauge-box">
                      <span className="gauge-label">Audio Peak (dBFS)</span>
                      <span
                        className="gauge-val"
                        style={{ color: (t.is_clipping ? "var(--clip-red)" : "var(--shure-green)") }}
                      >
                        {t.audio_level_dbfs ?? -18} dBFS
                      </span>
                    </div>
                  </div>

                  {/* VU Meter Bar */}
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "var(--text-muted)" }}>
                      <span>-60 dBFS</span>
                      <span>{t.is_clipping ? "CLIP!" : "VU METER"}</span>
                      <span>0 dBFS</span>
                    </div>
                    <div className="vu-meter-bar-container">
                      <div
                        className="vu-meter-fill"
                        style={{
                          width: `${vuPercent}%`,
                          background: t.is_clipping
                            ? "#ef4444"
                            : "linear-gradient(90deg, #10b981 70%, #f59e0b 90%, #ef4444 100%)"
                        }}
                      />
                    </div>
                  </div>

                  {/* Sub Info */}
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)" }}>
                    <span>Freq: {dev.frequency_mhz} MHz</span>
                    <span>Battery: {t.battery_percentage ?? 85}% ({t.battery_runtime_min ?? 400}m)</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Real-Time FFT Spectrum Visualizer */}
          <div className="spectrum-canvas-card">
            <div className="canvas-header">
              <span className="canvas-title">
                Live 16-Band FFT Audio Spectrum &amp; Oscilloscope ({selectedDevice?.channel_name})
              </span>
              <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                Sampling Rate: 48 kHz / 24-bit • Latency: {activeTelem.network_jitter_ms ?? 0.3}ms
              </span>
            </div>
            <canvas ref={canvasRef} className="spectrum-canvas" width={800} height={140} />
          </div>

          {/* Anomaly Simulation Drawer */}
          <div className="sim-controls-bar">
            <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", alignSelf: "center", marginRight: "8px" }}>
              TEST ANOMALY INJECTION:
            </span>
            <button className="btn-sim" onClick={() => handleSimulate("RF_COLLAPSE")}>
              ⚡ Trigger RF Fading (-86 dBm)
            </button>
            <button className="btn-sim" onClick={() => handleSimulate("PREAMP_CLIPPING")}>
              🚨 Trigger Preamp Overload (0 dBFS Clip)
            </button>
            <button className="btn-sim" onClick={() => handleSimulate("DANTE_JITTER")}>
              🌐 Trigger Dante AoIP Jitter (&gt;5ms)
            </button>
          </div>
        </section>

        {/* Right: AI Diagnostics & Automated Remediation */}
        <aside className="diagnostics-sidebar">
          <div className="sidebar-heading">
            <span className="sidebar-title-text">AI Diagnostic Center</span>
            <ShieldAlert size={18} color="var(--shure-green)" />
          </div>

          <div className="diagnostics-content">
            {diagnostics.length === 0 ? (
              <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "13px", padding: "32px 16px" }}>
                All networked audio nodes are operating within nominal RF, DSP, and Dante sync specifications.
              </div>
            ) : (
              diagnostics.map((report) => (
                <div key={report.id} className={`report-card ${!report.applied ? "unresolved" : ""}`}>
                  <div className="report-header">
                    <span className="report-reason-badge">{report.trigger_reason}</span>
                    <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                      Confidence: {Math.round((report.diagnostic_confidence || report.ai_confidence || 0.95) * 100)}%
                    </span>
                  </div>

                  <div className="report-body">
                    <strong>Root Cause:</strong> {report.root_cause_analysis}
                  </div>

                  <div className="remediation-box">
                    <strong>Remediation Plan:</strong> {report.remediation_plan}
                  </div>

                  {!report.applied ? (
                    <button className="btn-remediate" onClick={() => handleApplyRemediation(report.id)}>
                      <Zap size={14} />
                      Apply AI Recommended Fix
                    </button>
                  ) : (
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--shure-green)", fontSize: "12px", fontWeight: 700 }}>
                      <CheckCircle2 size={16} />
                      {report.verification_status === "VERIFIED" ? "Verified & Applied" : "Remediation Applied"}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
