from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings
from backend.app.models.device import Base, AudioDevice

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    seed_default_devices()

def seed_default_devices():
    db = SessionLocal()
    try:
        count = db.query(AudioDevice).count()
        if count == 0:
            devices = [
                AudioDevice(
                    id="shure-axient-ch1",
                    model_name="Shure Axient Digital AD4Q",
                    channel_name="Lead Vocal (Wireless Handheld)",
                    frequency_mhz=518.250,
                    ip_address="192.168.1.101",
                    dante_channel=1,
                    status="OPTIMAL",
                    pad_db=0,
                    is_muted=False
                ),
                AudioDevice(
                    id="shure-axient-ch2",
                    model_name="Shure Axient Digital AD4Q",
                    channel_name="Backing Vocal / Guitar",
                    frequency_mhz=522.400,
                    ip_address="192.168.1.101",
                    dante_channel=2,
                    status="OPTIMAL",
                    pad_db=0,
                    is_muted=False
                ),
                AudioDevice(
                    id="shure-mxa920-conf",
                    model_name="Shure MXA920 Ceiling Array",
                    channel_name="Executive Boardroom Center",
                    frequency_mhz=550.000,
                    ip_address="192.168.1.120",
                    dante_channel=3,
                    status="OPTIMAL",
                    pad_db=0,
                    is_muted=False
                ),
                AudioDevice(
                    id="shure-slxd-podium",
                    model_name="Shure SLX-D Digital Wireless",
                    channel_name="Main Stage Podium Mic",
                    frequency_mhz=536.800,
                    ip_address="192.168.1.105",
                    dante_channel=4,
                    status="WARNING",
                    pad_db=0,
                    is_muted=False
                ),
            ]
            db.add_all(devices)
            db.commit()
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
