import pytest
from app.core.security import encrypt_token, decrypt_token
from app.services.google_auth_service import GoogleAuthService
from app.database.repository import Repository


def test_token_encryption_and_decryption():
    secret_token = "ya29.a0AfH6SMA..."
    encrypted = encrypt_token(secret_token)
    assert encrypted != secret_token
    assert isinstance(encrypted, str)

    decrypted = decrypt_token(encrypted)
    assert decrypted == secret_token


def test_auth_status_empty(db_session):
    auth_service = GoogleAuthService(db_session)
    status = auth_service.get_auth_status()
    assert status["is_authenticated"] is False
    assert status["has_drive_scope"] is False
    assert status["has_youtube_scope"] is False


def test_auth_status_connected(db_session):
    repo = Repository(db_session)
    user = repo.upsert_user("creator@example.com", name="Creator")
    repo.save_credential(
        user_id=user.id,
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        token_expiry=None,
        scopes="https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/youtube.upload",
    )

    auth_service = GoogleAuthService(db_session)
    status = auth_service.get_auth_status()
    assert status["is_authenticated"] is True
    assert status["email"] == "creator@example.com"
    assert status["has_drive_scope"] is True
    assert status["has_youtube_scope"] is True
