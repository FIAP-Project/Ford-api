import pytest
from pydantic import ValidationError

from vehicle_service.schemas import QueryRequest


def test_valid_query() -> None:
    req = QueryRequest(
        brand="Ford",
        model="Ranger Raptor",
        version="2024",
        attributes=["motor", "potencia"],
    )
    assert req.brand == "Ford"
    assert req.attributes == ["motor", "potencia"]


def test_attribute_dedup_and_lower() -> None:
    req = QueryRequest(
        brand="Ford",
        model="Ranger",
        version="2024",
        attributes=["Motor", "motor", "Potencia"],
    )
    assert req.attributes == ["motor", "potencia"]


def test_rejects_too_many_attributes() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(
            brand="Ford",
            model="Ranger",
            version="2024",
            attributes=[f"attr-{i}" for i in range(31)],
        )


def test_rejects_command_injection_in_brand() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(
            brand="Ford; rm -rf /",
            model="Ranger",
            version="2024",
            attributes=["motor"],
        )


def test_rejects_oversized_attribute() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(
            brand="Ford",
            model="Ranger",
            version="2024",
            attributes=["a" * 200],
        )


def test_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(
            brand="Ford",
            model="Ranger",
            version="2024",
            attributes=["motor"],
            evil_field="x",  # type: ignore[call-arg]
        )
