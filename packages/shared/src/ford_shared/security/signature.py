"""HMAC-SHA256 payload signing for integrity verification."""

from __future__ import annotations

import hashlib
import hmac


def sign_payload(payload: bytes, secret: str) -> str:
    """Return hex HMAC-SHA256 of payload using the shared secret."""
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Constant-time verification of an HMAC signature."""
    expected = sign_payload(payload, secret)
    return hmac.compare_digest(expected, signature)
