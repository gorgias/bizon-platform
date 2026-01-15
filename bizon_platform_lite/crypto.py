"""Encryption utilities for securing pipeline configurations.

Uses Fernet symmetric encryption (AES-128-CBC with HMAC-SHA256).
The encryption key should be set via ENCRYPTION_KEY environment variable.

To generate a new key:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

import base64
import hashlib
import json
import os
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""

    pass


@lru_cache(maxsize=1)
def get_fernet() -> Fernet | None:
    """Get the Fernet instance for encryption/decryption.

    Returns None if no encryption key is configured, allowing the app
    to run without encryption (not recommended for production).
    """
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        return None

    # If the key is not a valid Fernet key (32 url-safe base64 bytes),
    # derive one from the provided key using SHA-256
    try:
        # Try using the key directly
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError):
        # Derive a valid Fernet key from the provided key
        derived = hashlib.sha256(key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(derived)
        return Fernet(fernet_key)


def encrypt_config(config: dict[str, Any]) -> str:
    """Encrypt a configuration dictionary.

    Args:
        config: The configuration dictionary to encrypt.

    Returns:
        Base64-encoded encrypted string prefixed with "enc:" marker.
        If no encryption key is set, returns JSON string prefixed with "plain:".

    Raises:
        EncryptionError: If encryption fails.
    """
    try:
        json_bytes = json.dumps(config, separators=(",", ":")).encode("utf-8")

        fernet = get_fernet()
        if fernet is None:
            # No encryption key - store as plain JSON with marker
            return f"plain:{base64.b64encode(json_bytes).decode()}"

        encrypted = fernet.encrypt(json_bytes)
        return f"enc:{encrypted.decode()}"

    except Exception as e:
        raise EncryptionError(f"Failed to encrypt config: {e}") from e


def decrypt_config(encrypted_data: str) -> dict[str, Any]:
    """Decrypt an encrypted configuration string.

    Args:
        encrypted_data: The encrypted string (with "enc:" or "plain:" prefix).

    Returns:
        The decrypted configuration dictionary.

    Raises:
        EncryptionError: If decryption fails or data is corrupted.
    """
    try:
        # Handle plain JSON (legacy or no encryption key)
        if encrypted_data.startswith("plain:"):
            json_bytes = base64.b64decode(encrypted_data[6:])
            return json.loads(json_bytes)

        # Handle encrypted data
        if encrypted_data.startswith("enc:"):
            fernet = get_fernet()
            if fernet is None:
                raise EncryptionError("Cannot decrypt: ENCRYPTION_KEY not set but data is encrypted")

            encrypted_bytes = encrypted_data[4:].encode()
            decrypted = fernet.decrypt(encrypted_bytes)
            return json.loads(decrypted)

        # Legacy: try to parse as raw JSON (for migration)
        try:
            if isinstance(encrypted_data, dict):
                return encrypted_data
            return json.loads(encrypted_data)
        except (json.JSONDecodeError, TypeError):
            raise EncryptionError("Unknown encryption format")

    except InvalidToken:
        raise EncryptionError("Failed to decrypt: invalid token (wrong key or corrupted data)")
    except Exception as e:
        if isinstance(e, EncryptionError):
            raise
        raise EncryptionError(f"Failed to decrypt config: {e}") from e


def is_encrypted(data: str | dict) -> bool:
    """Check if data is in encrypted format.

    Args:
        data: The data to check.

    Returns:
        True if the data appears to be encrypted.
    """
    if isinstance(data, dict):
        return False
    return isinstance(data, str) and data.startswith("enc:")


def encryption_enabled() -> bool:
    """Check if encryption is enabled (key is set)."""
    return get_fernet() is not None
