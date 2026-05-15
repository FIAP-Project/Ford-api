"""JWT issuance and verification using HS256."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict

from ford_shared.security.rbac import Role


class TokenPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    sub: str
    email: str
    role: Role
    iat: int
    exp: int
    jti: str
    token_type: str = "access"


class InvalidTokenError(Exception):
    pass


class JWTService:
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_ttl_minutes: int = 15,
        refresh_token_ttl_days: int = 7,
    ) -> None:
        if not secret_key or len(secret_key) < 32:
            raise ValueError("JWT secret must be at least 32 chars")
        self._secret = secret_key
        self._alg = algorithm
        self._access_ttl = timedelta(minutes=access_token_ttl_minutes)
        self._refresh_ttl = timedelta(days=refresh_token_ttl_days)

    def issue_access(self, user_id: str, email: str, role: Role) -> tuple[str, str]:
        return self._issue(user_id, email, role, self._access_ttl, "access")

    def issue_refresh(self, user_id: str, email: str, role: Role) -> tuple[str, str]:
        return self._issue(user_id, email, role, self._refresh_ttl, "refresh")

    def _issue(
        self,
        user_id: str,
        email: str,
        role: Role,
        ttl: timedelta,
        token_type: str,
    ) -> tuple[str, str]:
        now = datetime.now(UTC)
        jti = str(uuid4())
        payload = {
            "sub": user_id,
            "email": email,
            "role": role.value,
            "iat": int(now.timestamp()),
            "exp": int((now + ttl).timestamp()),
            "jti": jti,
            "token_type": token_type,
        }
        token = jwt.encode(payload, self._secret, algorithm=self._alg)
        return token, jti

    def decode(self, token: str, *, expected_type: str = "access") -> TokenPayload:
        try:
            raw = jwt.decode(token, self._secret, algorithms=[self._alg])
        except JWTError as exc:
            raise InvalidTokenError("Invalid or expired token") from exc

        if raw.get("token_type") != expected_type:
            raise InvalidTokenError("Wrong token type")

        return TokenPayload(**raw)
