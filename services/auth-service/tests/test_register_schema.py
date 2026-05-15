import pytest
from pydantic import ValidationError

from auth_service.schemas import LoginRequest, RegisterRequest


def test_valid_register() -> None:
    req = RegisterRequest(
        email="user@example.com",
        password="Strong#Pass123!",
        full_name="John Doe",
    )
    assert req.email == "user@example.com"


def test_weak_password_rejected() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(email="u@x.com", password="weak")


def test_password_without_symbol_rejected() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(email="u@x.com", password="OnlyLetters12345")


def test_password_without_digit_rejected() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(email="u@x.com", password="OnlyLetters!?#")


def test_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="u@x.com",
            password="Strong#Pass123!",
            evil="x",  # type: ignore[call-arg]
        )


def test_invalid_email_rejected() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(email="not-an-email", password="Strong#Pass123!")


def test_login_minimal() -> None:
    req = LoginRequest(email="u@x.com", password="x")
    assert req.password == "x"
