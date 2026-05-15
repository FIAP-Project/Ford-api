"""Password hashing using bcrypt directly.

Notes:
- bcrypt has a hard 72-byte limit on the password input. To avoid silent truncation
  we pre-hash the password with SHA-256 (32 bytes), then base64-encode (44 bytes),
  which keeps the input below 72 bytes regardless of user input length.
- This is a well-known pattern (e.g. how Dropbox handles it).
"""

from __future__ import annotations

import base64
import hashlib

import bcrypt


def _prepare(plain: str) -> bytes:
    digest = hashlib.sha256(plain.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(plain: str) -> str:
    prepared = _prepare(plain)
    return bcrypt.hashpw(prepared, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
