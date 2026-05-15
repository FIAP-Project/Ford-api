from vehicle_service.services.claude_client import ClaudeSpec
from vehicle_service.services.specs_normalizer import normalize_specs


def test_normalize_returns_exactly_requested_attributes_in_order() -> None:
    requested = ["motor", "potencia", "torque maximo"]
    from_claude = [
        ClaudeSpec(attribute="potencia", value="397cv", available=True),
        ClaudeSpec(attribute="motor", value="V6 3.0L", available=True),
    ]
    out = normalize_specs(requested, from_claude)
    assert [s.attribute for s in out] == requested


def test_missing_attribute_filled_with_unavailable() -> None:
    out = normalize_specs(
        ["preco"],
        [],
    )
    assert len(out) == 1
    assert out[0].attribute == "preco"
    assert out[0].value is None
    assert out[0].available is False


def test_empty_string_value_becomes_unavailable() -> None:
    out = normalize_specs(
        ["torque"],
        [ClaudeSpec(attribute="torque", value="   ", available=True)],
    )
    assert out[0].value is None
    assert out[0].available is False


def test_case_insensitive_match() -> None:
    out = normalize_specs(
        ["Motor"],
        [ClaudeSpec(attribute="motor", value="V6", available=True)],
    )
    assert out[0].value == "V6"
    assert out[0].attribute == "Motor"


def test_attributes_with_unknown_keys_are_ignored() -> None:
    out = normalize_specs(
        ["motor"],
        [
            ClaudeSpec(attribute="motor", value="V6", available=True),
            ClaudeSpec(attribute="aleatorio", value="X", available=True),
        ],
    )
    assert len(out) == 1
    assert out[0].attribute == "motor"
