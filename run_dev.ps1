# SonicPulse One-Click Launcher (PowerShell)
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Starting SonicPulse Platform              " -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan

$root = $PSScriptRoot

# 1. Start Backend with WebSockets
Write-Host "[1/2] Launching FastAPI + WebSocket backend on http://localhost:8000..." -ForegroundColor Yellow
$backendJob = Start-Process -FilePath "$root\backend\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn backend.app.main:app --reload --port 8000" -WorkingDirectory $root -PassThru

Start-Sleep -Seconds 2

# 2. Start Frontend
Write-Host "[2/2] Launching Vite React Dashboard on http://localhost:5173..." -ForegroundColor Yellow
Set-Location "$root\frontend"
npm run dev
