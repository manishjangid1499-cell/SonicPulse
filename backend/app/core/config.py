import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    PROJECT_NAME: str = "SonicPulse"
    API_PREFIX: str = "/api"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/sonicpulse.db")
    TELEMETRY_INTERVAL_MS: int = int(os.getenv("TELEMETRY_INTERVAL_MS", "250"))
    
    # Unified Audio & RF Engineering Thresholds
    RF_RSSI_CRITICAL_DBM: float = -80.0
    RF_SNR_CRITICAL_DB: float = 10.0
    AUDIO_CLIP_THRESHOLD_DBFS: float = -0.2
    DANTE_JITTER_THRESHOLD_MS: float = 2.0
    ALERT_DEDUPLICATION_COOLDOWN_SEC: float = 10.0

    CORS_ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

settings = Settings()
