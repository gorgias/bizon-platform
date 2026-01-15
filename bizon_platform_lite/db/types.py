"""Custom SQLAlchemy types for encrypted data."""

from typing import Any

from sqlalchemy import Text, TypeDecorator

from bizon_platform_lite.crypto import decrypt_config, encrypt_config


class EncryptedJSON(TypeDecorator):
    """SQLAlchemy type that encrypts JSON data at rest.

    Data is encrypted using Fernet (AES-128-CBC) when written to the database
    and decrypted when read. The encryption key is loaded from the
    ENCRYPTION_KEY environment variable.

    If no encryption key is set, data is stored as base64-encoded JSON
    with a "plain:" prefix (not recommended for production).

    Usage:
        class Pipeline(Base):
            config: Mapped[dict] = mapped_column(EncryptedJSON, nullable=False)
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: dict | None, dialect: Any) -> str | None:
        """Encrypt the value before storing in the database."""
        if value is None:
            return None
        return encrypt_config(value)

    def process_result_value(self, value: str | None, dialect: Any) -> dict | None:
        """Decrypt the value when reading from the database."""
        if value is None:
            return None
        return decrypt_config(value)
