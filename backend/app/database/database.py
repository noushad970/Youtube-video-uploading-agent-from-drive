from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.database.models import Base, AgentSettings

# SQLite requires check_same_thread=False for multi-threaded FastAPI/Scheduler access
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables and seed initial default settings if empty."""
    Base.metadata.create_all(bind=engine)
    
    with SessionLocal() as db:
        existing_settings = db.query(AgentSettings).first()
        if not existing_settings:
            default_settings = AgentSettings(
                enabled=False,
                interval_minutes=360,
                privacy_status=settings.DEFAULT_PRIVACY_STATUS,
                category_id=settings.DEFAULT_CATEGORY_ID,
                generate_title=True,
                generate_description=True,
                generate_tags=True,
                ollama_model=settings.OLLAMA_MODEL,
                max_retries=settings.MAX_RETRIES,
                delete_after_upload=settings.DELETE_AFTER_UPLOAD,
                fallback_if_ai_unavailable=settings.FALLBACK_IF_AI_UNAVAILABLE,
            )
            db.add(default_settings)
            db.commit()
