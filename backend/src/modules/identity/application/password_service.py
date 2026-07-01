"""PasswordService for secure password hashing using PBKDF2-SHA-256."""

from __future__ import annotations

import hashlib
import secrets


class PasswordService:
    """Password hashing and verification using PBKDF2-SHA-256.

    Format: ``salt$iterations$hash`` where salt is 64-char hex
    and hash is 64-char hex (32 bytes each).

    ponytail: PBKDF2 via stdlib is adequate for self-hosted HR MVP.
    Upgrade to argon2 if compliance audit requires it.
    """

    _ITERATIONS = 600_000
    _SALT_BYTES = 32
    _HASH_BYTES = 32
    _SEPARATOR = "$"

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash a password and return the encoded string."""
        salt = secrets.token_hex(cls._SALT_BYTES)
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("ascii"),
            cls._ITERATIONS,
            dklen=cls._HASH_BYTES,
        )
        return cls._SEPARATOR.join([salt, str(cls._ITERATIONS), dk.hex()])

    @classmethod
    def verify_password(cls, password: str, encoded: str) -> bool:
        """Verify a password against an encoded hash from ``hash_password``."""
        try:
            salt, iterations_str, stored_hash = encoded.split(cls._SEPARATOR)
        except (ValueError, AttributeError):
            return False

        try:
            iterations = int(iterations_str)
        except ValueError:
            return False

        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("ascii"),
            iterations,
            dklen=cls._HASH_BYTES,
        )
        return dk.hex() == stored_hash
