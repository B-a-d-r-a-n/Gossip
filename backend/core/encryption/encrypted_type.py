from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator
from core.encryption.encryptor import get_fernet
class EncryptedString(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        return get_fernet().encrypt(value.encode()).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        return get_fernet().decrypt(value.encode()).decode()