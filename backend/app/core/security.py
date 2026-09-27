import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    """Derive a 32-byte url-safe base64-encoded key from SECRET_KEY."""
    raw_key = settings.SECRET_KEY.encode("utf-8")
    derived_32 = hashlib.sha256(raw_key).digest()
    fernet_key = base64.urlsafe_b64encode(derived_32)
    return Fernet(fernet_key)


def encrypt_token(plain_token: str | None) -> str | None:
    """Encrypt a token string before storing in database."""
    if not plain_token:
        return None
    f = _get_fernet()
    encrypted_bytes = f.encrypt(plain_token.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_token(encrypted_token: str | None) -> str | None:
    """Decrypt a stored token string."""
    if not encrypted_token:
        return None
    try:
        f = _get_fernet()
        decrypted_bytes = f.decrypt(encrypted_token.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception:
        # Fallback if token was stored in plain text during dev or legacy migration
        return encrypted_token
