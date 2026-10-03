"""
Security & Encryption Utilities for DIANISMA.GR.
Provides Fernet symmetric field-level encryption for sensitive database fields.
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.db import models


def _get_fernet_key() -> bytes:
    """
    Retrieve FERNET_KEY from environment/settings or derive it deterministically
    from SECRET_KEY using PBKDF2HMAC.
    """
    env_key = getattr(settings, 'FERNET_KEY', None) or os.environ.get('FERNET_KEY')
    if env_key:
        if isinstance(env_key, str):
            return env_key.encode('utf-8')
        return env_key

    # Fallback: derive a 32-byte key from Django's SECRET_KEY
    secret = settings.SECRET_KEY.encode('utf-8')
    salt = b'dianisma_security_salt_2024'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret))


def get_fernet() -> Fernet:
    """Return a Fernet cipher instance."""
    return Fernet(_get_fernet_key())


def encrypt_sensitive_data(plaintext: str) -> str:
    """Encrypt plaintext string using Fernet symmetric encryption."""
    if not plaintext:
        return ''
    f = get_fernet()
    encrypted_bytes = f.encrypt(plaintext.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')


def decrypt_sensitive_data(ciphertext: str) -> str:
    """Decrypt ciphertext string using Fernet symmetric encryption."""
    if not ciphertext:
        return ''
    try:
        f = get_fernet()
        decrypted_bytes = f.decrypt(ciphertext.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception:
        # Fallback if unencrypted legacy data or decryption error
        return ciphertext


class EncryptedCharField(models.CharField):
    """CharField that transparently encrypts data on write and decrypts on read."""

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value:
            return encrypt_sensitive_data(str(value))
        return value

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_sensitive_data(value)

    def to_python(self, value):
        value = super().to_python(value)
        if value is None or not isinstance(value, str):
            return value
        # If it looks like a Fernet token (starts with gAAAAA), attempt decrypt
        if value.startswith('gAAAAA'):
            return decrypt_sensitive_data(value)
        return value


class EncryptedTextField(models.TextField):
    """TextField that transparently encrypts data on write and decrypts on read."""

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value:
            return encrypt_sensitive_data(str(value))
        return value

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_sensitive_data(value)

    def to_python(self, value):
        value = super().to_python(value)
        if value is None or not isinstance(value, str):
            return value
        if value.startswith('gAAAAA'):
            return decrypt_sensitive_data(value)
        return value
