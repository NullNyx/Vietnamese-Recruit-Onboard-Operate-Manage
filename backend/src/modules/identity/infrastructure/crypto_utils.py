"""AES-256-GCM encryption utilities for OAuth token storage."""

import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True)
class VersionedSecret:
    format_version: int
    key_version: int
    ciphertext: str


class CryptoUtils:
    """AES-256-GCM encryption for OAuth tokens."""

    _NONCE_SIZE = 12
    _TAG_SIZE = 16
    _FORMAT_VERSION = 1

    def __init__(self, encryption_key_b64: str, *, key_version: int = 1) -> None:
        key_bytes = base64.b64decode(encryption_key_b64)
        if len(key_bytes) != 32:
            raise ValueError(f"Encryption key must be exactly 32 bytes, got {len(key_bytes)} bytes")
        self._aesgcm = AESGCM(key_bytes)
        self._key_version = key_version

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(self._NONCE_SIZE)
        ciphertext_and_tag = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext_and_tag).decode("ascii")

    def encrypt_versioned(self, plaintext: str) -> VersionedSecret:
        return VersionedSecret(self._FORMAT_VERSION, self._key_version, self.encrypt(plaintext))

    def decrypt(self, ciphertext: str) -> str:
        combined = base64.b64decode(ciphertext)
        if len(combined) < self._NONCE_SIZE + self._TAG_SIZE:
            raise ValueError(f"Ciphertext too short: expected at least {self._NONCE_SIZE + self._TAG_SIZE} bytes, got {len(combined)}")
        nonce = combined[: self._NONCE_SIZE]
        plaintext_bytes = self._aesgcm.decrypt(nonce, combined[self._NONCE_SIZE :], None)
        return plaintext_bytes.decode("utf-8")

    def redact(self, secret: str | None) -> str | None:
        if secret is None:
            return None
        if len(secret) <= 4:
            return "*" * len(secret)
        return f"{'*' * (len(secret) - 4)}{secret[-4:]}"
