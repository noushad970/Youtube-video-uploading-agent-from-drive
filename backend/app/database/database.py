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


from sqlalchemy import text

def _migrate_db() -> None:
    """Safely apply missing column migrations and enforce modern defaults."""
    with engine.connect() as conn:
        migrations = [
            ("uploads", "thumbnail_path", "VARCHAR(1024)"),
            ("agent_settings", "generate_thumbnail", "BOOLEAN DEFAULT 1"),
            ("agent_settings", "ai_provider", "VARCHAR(64) DEFAULT 'gemini'"),
            ("agent_settings", "gemini_api_key", "VARCHAR(255)"),
            ("agent_settings", "gemini_model", "VARCHAR(128) DEFAULT 'gemini-3.5-flash-lite'"),
            ("agent_settings", "gemini_image_model", "VARCHAR(128) DEFAULT 'imagen-3.0-generate-002'"),
        ]
        for table, col, col_type in migrations:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass

        # Data migrations: Ensure modern models (3.5+) and active features
        try:
            # Upgrade deprecated 2.5 or older models
            conn.execute(text(
                "UPDATE agent_settings SET gemini_model = 'gemini-3.5-flash-lite' "
                "WHERE gemini_model IS NULL OR gemini_model LIKE '%2.5%' OR gemini_model LIKE '%1.5%'"
            ))
            # Enable thumbnail, description, tags by default
            conn.execute(text(
                "UPDATE agent_settings SET generate_thumbnail = 1, generate_description = 1, generate_tags = 1, generate_title = 1 "
                "WHERE generate_thumbnail IS NULL OR generate_description IS NULL OR generate_tags IS NULL"
            ))
            # Sync API key from environment if currently empty or invalid placeholder
            if settings.GEMINI_API_KEY:
                conn.execute(
                    text(
                        "UPDATE agent_settings SET gemini_api_key = :key "
                        "WHERE gemini_api_key IS NULL OR gemini_api_key = '' OR gemini_api_key LIKE 'Option%'"
                    ),
                    {"key": settings.GEMINI_API_KEY},
                )
            conn.commit()
        except Exception:
            pass


def init_db() -> None:
    """Create all tables and seed initial default settings if empty."""
    Base.metadata.create_all(bind=engine)
    _migrate_db()
    
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
                generate_thumbnail=settings.GENERATE_THUMBNAIL,
                ai_provider=settings.AI_PROVIDER,
                gemini_api_key=settings.GEMINI_API_KEY or None,
                gemini_model=settings.GEMINI_MODEL,
                gemini_image_model=settings.GEMINI_IMAGE_MODEL,
                ollama_model=settings.OLLAMA_MODEL,
                max_retries=settings.MAX_RETRIES,
                delete_after_upload=settings.DELETE_AFTER_UPLOAD,
                fallback_if_ai_unavailable=settings.FALLBACK_IF_AI_UNAVAILABLE,
            )
            db.add(default_settings)
            db.commit()
