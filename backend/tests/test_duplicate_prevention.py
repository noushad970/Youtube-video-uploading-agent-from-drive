import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from app.database.repository import Repository
from app.services.upload_service import UploadService
from app.services.scheduler_service import SchedulerService


def test_duplicate_upload_prevention(db_session, tmp_path):
    repo = Repository(db_session)
    video = repo.upsert_video_from_drive("drive_file_99", "tutorial.mp4", "video/mp4", 5000)
    
    # Create fake local file
    test_file = tmp_path / "test_video.mp4"
    test_file.write_bytes(b"dummy video content")

    upload_service = UploadService(db_session)
    mock_yt = MagicMock()
    mock_yt.upload_video.return_value = "yt_id_12345"
    upload_service.youtube_service = mock_yt

    # First upload
    rec1 = upload_service.process_upload_with_retry(
        video=video,
        file_path=test_file,
        title="Tutorial Video",
        description="Description",
    )
    assert rec1.status == "uploaded"
    assert rec1.youtube_video_id == "yt_id_12345"
    assert mock_yt.upload_video.call_count == 1

    # Second upload attempt on same video must be safely prevented
    rec2 = upload_service.process_upload_with_retry(
        video=video,
        file_path=test_file,
        title="Tutorial Video",
        description="Description",
    )
    assert rec2.status == "uploaded"
    assert rec2.youtube_video_id == "yt_id_12345"
    # youtube_service.upload_video should NOT have been called a second time
    assert mock_yt.upload_video.call_count == 1


def test_scheduler_lock_mechanism():
    status = SchedulerService.get_status()
    assert "scheduler_running" in status
    assert "is_job_currently_executing" in status
