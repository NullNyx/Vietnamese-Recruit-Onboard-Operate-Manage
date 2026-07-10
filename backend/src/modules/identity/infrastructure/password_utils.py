"""Password hashing helpers for local auth."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

_PBKDF2_ALGORITHM = "sha256"
_PBKDF2_ITERATIONS = 310_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Hash ``password`` with PBKDF2-HMAC-SHA256.

    Format: ``pbkdf2_sha256$<iterations>$<salt>$<hash>``.
    """
    salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${_PBKDF2_ITERATIONS}$"
        f"{base64.urlsafe_b64encode(salt).decode('ascii')}$"
        f"{base64.urlsafe_b64encode(derived).decode('ascii')}"
    )


def verify_password(password: str, hashed: str) -> bool:
    """Verify ``password`` against stored hash."""
    try:
        scheme, iterations_raw, salt_raw, digest_raw = hashed.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iterations_raw)
        salt = base64.urlsafe_b64decode(salt_raw.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_raw.encode("ascii"))
    except (ValueError, TypeError, base64.binascii.Error):
        return False

    candidate = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(candidate, expected)


def generate_temporary_password(length: int = 12) -> str:
    """Generate human-readable temporary password."""
    if length < 10:
        length = 10
    raw = secrets.token_urlsafe(length)
    return raw[:length]
