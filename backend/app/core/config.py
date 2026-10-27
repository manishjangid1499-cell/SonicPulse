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
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", os.getenv("GEMINI_API_KEY", "")))
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")

settings = Settings()
