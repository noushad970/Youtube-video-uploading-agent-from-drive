import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from app.core.config import settings

logger = logging.getLogger("youtube_agent")


class DatabaseLogHandler(logging.Handler):
    """Custom logging handler to persist application logs into DB for the web dashboard."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            from app.database.database import SessionLocal
            from app.database.models import LogEntry

            msg = self.format(record)
            details = None
            if record.exc_info:
                import traceback
                details = "".join(traceback.format_exception(*record.exc_info))

            with SessionLocal() as db:
                log_entry = LogEntry(
                    level=record.levelname,
                    message=record.getMessage(),
                    details=details or (msg if msg != record.getMessage() else None),
                    created_at=datetime.now(timezone.utc),
                )
                db.add(log_entry)
                db.commit()
        except Exception:
            # Prevent logging errors from crashing application
            pass


def setup_logging() -> logging.Logger:
    """Configure structured logging to console, file, and database."""
    log_dir = Path(settings.LOG_DIRECTORY)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "agent.log"

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Avoid duplicate handlers on reloads
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # 1. Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 2. Rotating File Handler (10MB max, keep 5 backups)
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # 3. Database Handler
        db_handler = DatabaseLogHandler()
        db_handler.setLevel(log_level)
        db_handler.setFormatter(formatter)
        logger.addHandler(db_handler)

    return logger
