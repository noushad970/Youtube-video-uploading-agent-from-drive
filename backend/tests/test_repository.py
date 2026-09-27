import pytest
from app.database.repository import Repository
from app.database.models import Video, Upload


def test_settings_crud(repo: Repository):
    settings = repo.get_settings()
    assert settings.enabled is False
    assert settings.interval_minutes == 360

    updated = repo.update_settings(enabled=True, interval_minutes=120)
    assert updated.enabled is True
    assert updated.interval_minutes == 120


def test_video_upsert_and_stats(repo: Repository):
    v1 = repo.upsert_video_from_drive(
        drive_file_id="drive_1",
        file_name="gameplay_01.mp4",
        mime_type="video/mp4",
        size=1024 * 1024,
        folder_id="folder_abc",
    )
    assert v1.id is not None
    assert v1.status == "available"

    # Upsert again shouldn't duplicate
    v1_again = repo.upsert_video_from_drive(
        drive_file_id="drive_1",
        file_name="gameplay_01_renamed.mp4",
        mime_type="video/mp4",
        size=1024 * 1024,
        folder_id="folder_abc",
    )
    assert v1_again.id == v1.id
    assert v1_again.file_name == "gameplay_01_renamed.mp4"

    stats = repo.get_video_stats("folder_abc")
    assert stats["total"] == 1
    assert stats["uploaded"] == 0
    assert stats["remaining"] == 1


def test_select_random_unuploaded_video(repo: Repository):
    repo.upsert_video_from_drive("id_1", "video1.mp4", "video/mp4", 1000, "f1")
    repo.upsert_video_from_drive("id_2", "video2.mp4", "video/mp4", 2000, "f1")
    repo.upsert_video_from_drive("id_3", "video3.mp4", "video/mp4", 3000, "f1")

    # Mark video1 as uploaded
    v1 = repo.get_video_by_drive_id("id_1")
    repo.update_video(v1.id, status="uploaded")
    repo.create_upload(v1.id, "Title 1")
    u1 = repo.db.query(Upload).filter(Upload.video_id == v1.id).first()
    repo.update_upload(u1.id, status="uploaded", youtube_video_id="yt_1")

    # Mark video2 as currently downloading/uploading
    v2 = repo.get_video_by_drive_id("id_2")
    repo.update_video(v2.id, status="uploading")

    # Only video3 should be chosen
    selected = repo.select_random_unuploaded_video("f1")
    assert selected is not None
    assert selected.drive_file_id == "id_3"

    # Once video3 is also uploaded, selection should return None
    repo.update_video(selected.id, status="uploaded")
    repo.create_upload(selected.id, "Title 3")
    u3 = repo.db.query(Upload).filter(Upload.video_id == selected.id).first()
    repo.update_upload(u3.id, status="uploaded", youtube_video_id="yt_3")

    none_selected = repo.select_random_unuploaded_video("f1")
    assert none_selected is None
