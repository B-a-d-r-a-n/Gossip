import base64
from cryptography.fernet import Fernet, MultiFernet
from core.config import settings


def validate_encryption_keys(keys: list[str]):
    for k in keys:
        if len(k) != 44:
            raise ValueError("Fernet keys must be exactly 44 characters long.")
        try:
            base64.urlsafe_b64decode(k)
        except Exception:
            raise ValueError("Fernet keys must be valid url-safe base64.")


def get_fernet() -> MultiFernet:
    """
    MultiFernet supports key rotation: primary key encrypts new data,
    all keys can decrypt old data. Rotate by prepending new key to ENCRYPTION_KEYS list.
    """
    keys = settings.encryption_keys_list
    validate_encryption_keys(keys)
    fernet_keys = [Fernet(k) for k in keys]
    return MultiFernet(fernet_keys)
