import pytest

from ford_shared.security import Role
from ford_shared.security.jwt import InvalidTokenError, JWTService


@pytest.fixture
def jwt() -> JWTService:
    return JWTService(secret_key="a" * 32, access_token_ttl_minutes=15)


def test_issue_and_decode_access(jwt: JWTService) -> None:
    token, jti = jwt.issue_access("user-1", "u@x.com", Role.USER)
    decoded = jwt.decode(token, expected_type="access")
    assert decoded.sub == "user-1"
    assert decoded.email == "u@x.com"
    assert decoded.role == Role.USER
    assert decoded.jti == jti


def test_decode_rejects_wrong_token_type(jwt: JWTService) -> None:
    token, _ = jwt.issue_refresh("user-1", "u@x.com", Role.USER)
    with pytest.raises(InvalidTokenError):
        jwt.decode(token, expected_type="access")


def test_decode_rejects_tampered_token(jwt: JWTService) -> None:
    token, _ = jwt.issue_access("user-1", "u@x.com", Role.USER)
    tampered = token[:-2] + "ZZ"
    with pytest.raises(InvalidTokenError):
        jwt.decode(tampered, expected_type="access")


def test_short_secret_rejected() -> None:
    with pytest.raises(ValueError):
        JWTService(secret_key="too-short")
