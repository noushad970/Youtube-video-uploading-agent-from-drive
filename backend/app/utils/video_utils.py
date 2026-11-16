import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.logging_config import logger


def extract_video_metadata(file_path: str | Path) -> Dict[str, Any]:
    """
    Extract technical video metadata using ffprobe.
    Returns duration, resolution, fps, video_codec, audio_codec, and size.
    """
    path = Path(file_path)
    if not path.exists():
        return {}

    result: Dict[str, Any] = {
        "file_size": path.stat().st_size,
        "duration": None,
        "resolution": None,
        "fps": None,
        "video_codec": None,
        "audio_codec": None,
        "has_audio": False,
    }

    try:
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            format_info = data.get("format", {})
            if "duration" in format_info:
                result["duration"] = int(float(format_info["duration"]))

            streams = data.get("streams", [])
            for stream in streams:
                codec_type = stream.get("codec_type")
                if codec_type == "video" and not result["video_codec"]:
                    result["video_codec"] = stream.get("codec_name")
                    width = stream.get("width")
                    height = stream.get("height")
                    if width and height:
                        result["resolution"] = f"{width}x{height}"
                    
                    r_frame_rate = stream.get("r_frame_rate", "")
                    if "/" in r_frame_rate:
                        num, den = r_frame_rate.split("/")
                        if float(den) > 0:
                            result["fps"] = f"{round(float(num) / float(den), 2)}"
                    elif r_frame_rate:
                        result["fps"] = r_frame_rate

                elif codec_type == "audio" and not result["audio_codec"]:
                    result["audio_codec"] = stream.get("codec_name")
                    result["has_audio"] = True

    except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"ffprobe metadata extraction failed for {path.name}: {e}")

    return result


def extract_video_thumbnail(
    video_path: str | Path,
    output_image_path: str | Path,
    timestamp_sec: int = 1,
) -> Optional[str]:
    """Generate a thumbnail image from video at specified timestamp."""
    v_path = Path(video_path)
    out_path = Path(output_image_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not v_path.exists():
        return None

    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            str(timestamp_sec),
            "-i",
            str(v_path),
            "-vframes",
            "1",
            "-q:v",
            "2",
            "-update",
            "1",
            str(out_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0 and out_path.exists() and out_path.stat().st_size > 500:
            return str(out_path.resolve())
    except Exception as e:
        logger.warning(f"Thumbnail extraction failed for {v_path.name}: {e}")

    return None


def extract_and_enhance_thumbnail(
    video_path: str | Path,
    output_image_path: str | Path,
    timestamp_sec: Optional[int] = None,
    title: Optional[str] = None,
) -> Optional[str]:
    """
    Generate an enhanced, eye-catching 16:9 YouTube thumbnail (1280x720) from video file using FFmpeg.
    Chooses an optimal frame (avoiding initial black frames), standardizes to 1280x720 16:9,
    and applies a vibrance/contrast boost for high CTR.
    """
    v_path = Path(video_path)
    out_path = Path(output_image_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not v_path.exists():
        return None

    # Determine optimal frame timestamp (15% in or at least 2s)
    if timestamp_sec is None:
        meta = extract_video_metadata(v_path)
        duration = meta.get("duration") or 0
        if duration > 10:
            timestamp_sec = min(int(duration * 0.15), 30)
        elif duration > 2:
            timestamp_sec = 1
        else:
            timestamp_sec = 0

    try:
        # Scale to 1280x720 (standard 16:9 YouTube resolution), pad with black if needed, boost contrast & saturation
        vf_filter = (
            "scale=1280:720:force_original_aspect_ratio=decrease,"
            "pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,"
            "eq=contrast=1.12:brightness=0.02:saturation=1.2"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(timestamp_sec),
            "-i", str(v_path),
            "-vframes", "1",
            "-vf", vf_filter,
            "-q:v", "2",
            "-update", "1",
            str(out_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0 and out_path.exists() and out_path.stat().st_size > 1000:
            logger.info(f"Successfully generated enhanced video thumbnail: {out_path}")
            return str(out_path.resolve())
        else:
            logger.warning(f"FFmpeg enhanced filter failed (code {proc.returncode}): {proc.stderr}")
    except Exception as e:
        logger.warning(f"Enhanced thumbnail extraction failed: {e}")

    # Fallback to standard frame extraction
    return extract_video_thumbnail(v_path, out_path, timestamp_sec=timestamp_sec or 1)


def create_graphic_thumbnail(
    output_image_path: str | Path,
    title: str = "YouTube Video",
) -> Optional[str]:
    """Create a high-resolution 1280x720 16:9 branded placeholder thumbnail using FFmpeg."""
    out_path = Path(output_image_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "lavfi",
            "-i", "color=c=0x0f172a:s=1280x720:d=1",
            "-vframes", "1",
            "-q:v", "2",
            "-update", "1",
            str(out_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if proc.returncode == 0 and out_path.exists():
            return str(out_path.resolve())
    except Exception as e:
        logger.warning(f"Graphic thumbnail generation failed: {e}")
    return None
