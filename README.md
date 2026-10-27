<div align="center">

# 🎙️ SonicPulse
### Real-Time Networked Audio Device Telemetry &amp; AI Diagnostic Platform

[![CI Pipeline](https://img.shields.io/badge/CI-GitHub_Actions-brightgreen?logo=github-actions&style=for-the-badge)](.github/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&style=for-the-badge)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&style=for-the-badge)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&style=for-the-badge)](https://react.dev/)
[![WebSockets](https://img.shields.io/badge/WebSockets-Real--Time_4Hz-orange?logo=websocket&style=for-the-badge)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&style=for-the-badge)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br/>

<p align="center">
  <strong>An enterprise-grade full-stack platform engineered to monitor mission-critical networked audio hardware fleets (Shure Axient Digital, MXA920, SLX-D), stream high-frequency RF and DSP telemetry over full-duplex WebSockets, and autonomously diagnose RF fading, pre-amplifier clipping, and Dante AoIP network jitter with sub-100ms automated remediation.</strong>
</p>

---

### 🖥️ Live Telemetry &amp; Diagnostic Platform Console

<img src="docs/assets/dashboard-preview.svg" alt="SonicPulse Platform Dashboard" width="100%"/>

</div>

---

## 📌 Executive Summary

Live performance venues, broadcast networks, and corporate boardrooms depend on mission-critical networked audio ecosystems such as **Shure Axient Digital**, **Microflex Advance MXA920**, and **SLX-D**. In live production environments, audio engineers face three primary failure modes:

1. **RF Multipath Interference & Carrier Collapse**: Crowded UHF spectrum, 5G cellular downlink carriers, or multi-path phase cancellations can cause the carrier Signal-to-Noise Ratio (SNR) to collapse, resulting in sudden digital audio muting.
2. **Acoustic Overload & Preamp ADC Clipping**: High Sound Pressure Level (SPL) vocal transients that exceed pre-amplifier analog headroom cause harsh digital square-wave clipping (>0 dBFS) and harmonic distortion.
3. **Dante / AES67 AoIP Network Jitter**: Synchronization clock drift across Gigabit switches (Precision Time Protocol PTP v2) exceeding 2.0 ms results in packet buffer under-runs and audible audio clicks.

**SonicPulse** solves this challenge by delivering a high-frequency real-time telemetry streaming pipeline and an automated **AI Diagnostic & Self-Healing Engine** that continuously detects anomalies, calculates intermodulation-free UHF backup channels, and executes single-click hardware remediation before audio dropouts occur.

---

## 📊 Live Audio Spectrum &amp; Oscilloscope Visualizer

SonicPulse features a hardware-accelerated **60 FPS HTML5 Canvas engine** that visualizes uncompressed 48 kHz / 24-bit audio signals across 16 FFT frequency spectrum bins and real-time sine oscilloscope waveforms:

<div align="center">
  <img src="docs/assets/spectrum-analyzer-preview.svg" alt="Live 16-Band FFT Audio Spectrum & Oscilloscope" width="100%"/>
</div>

---

## ⚡ Automated AI Diagnostic &amp; Self-Healing Flow

When an RF drop or audio clip occurs, the AI diagnostic engine detects the threshold violation within 250 milliseconds, diagnoses the root cause, and synthesizes a hardware remediation plan:

<div align="center">
  <img src="docs/assets/diagnostic-flow-preview.svg" alt="AI Diagnostic and Auto-Remediation Workflow" width="100%"/>
</div>

---

## 🏗️ System Architecture

```mermaid
flowchart LR
    subgraph Fleet ["Networked Audio Hardware Fleet"]
        Axient1["Shure Axient Digital AD4Q (Ch 1)"]
        Axient2["Shure Axient Digital AD4Q (Ch 2)"]
        MXA["Shure MXA920 Ceiling Array"]
        SLXD["Shure SLX-D Digital Wireless"]
    end

    subgraph Backend ["FastAPI Telemetry Hub & AI Engine"]
        Sim["Physics Simulation Engine<br/>(RF RSSI, dBFS, Dante AoIP, FFT)"]
        WS["WebSocket Streaming Server (4 Hz)"]
        Diag["AI Anomaly Diagnostic Engine"]
        DB[(SQLAlchemy ORM<br/>SQLite / PostgreSQL)]
    end

    subgraph Frontend ["React 19 Audio Console"]
        Canvas["60fps HTML5 Canvas<br/>(16-Band FFT Spectrum & Oscilloscope)"]
        Meters["Hardware VU Meters &amp; RF Gauges"]
        Fix["AI Diagnostic Drawer<br/>(One-Click Self-Healing)"]
    end

    Fleet --> Sim
    Sim --> WS
    Sim --> Diag
    Diag --> DB
    WS --> Canvas
    WS --> Meters
    Diag --> Fix
    Fix -->|"Remediation Action"| Backend
```

<div align="center">
  <img src="docs/assets/architecture.svg" alt="SonicPulse Architecture" width="90%"/>
</div>

---

## 🚀 Key Technical Features

### 1. High-Frequency Real-Time Telemetry Stream (WebSockets @ 4 Hz)
- Full-duplex WebSocket connection streaming real-time telemetry snapshots every 250ms per audio channel.
- **RF Wireless Telemetry**: RSSI signal strength (-90 dBm to -30 dBm), Carrier SNR (dB), UHF carrier frequency (MHz).
- **Audio DSP Telemetry**: Peak level in dBFS (-60 dBFS to 0 dBFS), clip state flag, Crest factor.
- **Network & Clock Sync**: Dante / AES67 AoIP packet drop percentage and PTP v2 network jitter in milliseconds.
- **Battery & Power**: Charge percentage and calculated runtime remaining in minutes.

### 2. 60 FPS HTML5 Canvas FFT Audio Spectrum & Oscilloscope
- Hardware-accelerated canvas visualizer rendering 16 FFT frequency bins in real time.
- Oscilloscope waveform tracking acoustic dynamics with instantaneous color-coded transitions to red upon pre-amp overload.
- Multi-segment LED VU meter with peak-hold indicators.

### 3. AI Diagnostic & Automated Remediation Engine
- **RF Carrier Fading / Intermod**: Detects RSSI drops below -80 dBm and SNR degradation (<10 dB). Analyzes clean UHF spectrum channels and recommends an intermodulation-free frequency (e.g. `548.750 MHz`).
- **ADC Preamp Clipping**: Detects sustained `0.0 dBFS` clipping. Recommends engaging the `-12 dB` analog hardware attenuator pad.
- **Single-Click Healing**: Operators can click **[⚡ Apply AI Recommended Fix]** to re-tune hardware parameters and restore nominal performance in under 100 milliseconds.

---

## 📂 Project Structure

```bash
SonicPulse/
├── .github/workflows/
│   └── ci.yml               # Automated CI/CD pipeline (Pytest + Vite Build)
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI REST & WebSocket endpoints
│   │   │   └── routes.py    # Hardware controls, telemetry, and diagnostics
│   │   ├── core/            # Config, settings, and database session
│   │   ├── models/          # SQLAlchemy ORM models (AudioDevice, Telemetry, Alert)
│   │   ├── schemas/         # Pydantic request/response validation schemas
│   │   └── services/        # Audio simulation & AI diagnostic engine
│   │       ├── simulator.py # Shure hardware physics simulator
│   │       └── diagnostics.py # Anomaly detection & auto-remediation
│   ├── tests/               # Backend Pytest test suite (100% passing)
│   ├── Dockerfile           # Backend container definition
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/                 # React 19 application
│   │   ├── App.jsx          # Live Audio Console & Canvas visualizer
│   │   ├── App.css          # Studio dark-theme stylesheet
│   │   └── main.jsx         # Vite entrypoint
│   ├── Dockerfile           # Multi-stage Nginx container build
│   └── package.json         # Node.js dependencies
├── docs/assets/             # Retina UI previews and architecture graphics
├── docker-compose.yml       # Full-stack container orchestration
├── run_dev.ps1              # One-click Windows development launcher
└── README.md                # Documentation & Architecture Guide
```

---

## ⚡ Quickstart Guide

### Option 1: Native Local Setup

#### Prerequisites
- **Python**: 3.10+ (tested on Python 3.12)
- **Node.js**: 18+ (tested on Node.js 24)

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```
Backend API will be live at: `http://localhost:8000` (Interactive API documentation at `http://localhost:8000/docs`).

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend UI will be live at: `http://localhost:5173`.

---

### Option 2: Docker Compose (Full Stack)

```bash
docker compose up --build
```
Access the application dashboard at `http://localhost:3000`.

---

## 🧪 Interactive Anomaly Injection & Remediation Demo

1. Open the web console at `http://localhost:5173`.
2. Notice the live 4Hz telemetry stream and animated 16-band audio spectrum.
3. Test failure modes using the **Anomaly Injection Bar** at the bottom:
   - Click **`⚡ Trigger RF Fading`**: Watch the RSSI gauge drop to `-86 dBm` and the card turn Red. The AI Diagnostic Center immediately reports **RF_INTERFERENCE** and calculates a clear backup frequency (`548.750 MHz`).
   - Click **`⚡ Apply AI Recommended Fix`**: The receiver immediately retunes, restoring RSSI to `-48 dBm` and health to **OPTIMAL**!
   - Click **`🚨 Trigger 0 dBFS Clip`**: Watch the VU meter max out into the red clip zone. Click **`⚡ Apply AI Recommended Fix`** to engage the `-12 dB` hardware pad.

---

## 📋 Running Automated Tests

Run the backend unit, integration, and diagnostic test suite:

```bash
# Windows PowerShell:
$env:PYTHONPATH = (Get-Location).Path
.\backend\.venv\Scripts\pytest backend/tests/ -v

# Linux/macOS:
# export PYTHONPATH=$(pwd)
# pytest backend/tests/ -v
```
*(All 5 test suites pass cleanly with 100% success rate).*

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
