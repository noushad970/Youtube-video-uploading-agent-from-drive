import os
import shutil
import re
from pathlib import Path
from app.core.logging_config import logger


def check_disk_space(required_bytes: int, target_dir: str = "./data/videos") -> bool:
    """Check if there is sufficient disk space available in target directory."""
    try:
        path = Path(target_dir).resolve()
        path.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(path)
        # Require at least required_bytes + 200MB buffer
        has_space = usage.free > (required_bytes + 200 * 1024 * 1024)
        if not has_space:
            logger.error(
                f"Insufficient disk space in {path}. Free: {format_bytes(usage.free)}, "
                f"Required: {format_bytes(required_bytes)}"
            )
        return has_space
    except Exception as e:
        logger.warning(f"Unable to verify disk space for {target_dir}: {e}")
        return True


def safe_delete_file(file_path: str | Path | None) -> bool:
    """Safely delete a local temporary file."""
    if not file_path:
        return False
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            logger.info(f"Cleaned up temporary local file: {path.name}")
            return True
        return False
    except Exception as e:
        logger.warning(f"Failed to delete local file {file_path}: {e}")
        return False


def sanitize_filename(name: str) -> str:
    """Sanitize string to be safe as a cross-platform filename."""
    # Remove characters invalid in Windows / POSIX file systems
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "video.mp4"


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human readable string (KB, MB, GB)."""
    if size_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"
