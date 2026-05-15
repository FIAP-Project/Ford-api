from ford_shared.security.signature import sign_payload, verify_signature


def test_sign_and_verify_roundtrip() -> None:
    payload = b'{"foo":"bar"}'
    secret = "a" * 32
    signature = sign_payload(payload, secret)
    assert verify_signature(payload, signature, secret) is True


def test_verify_rejects_tampered_payload() -> None:
    payload = b'{"foo":"bar"}'
    secret = "a" * 32
    signature = sign_payload(payload, secret)
    assert verify_signature(b'{"foo":"BAZ"}', signature, secret) is False


def test_verify_rejects_wrong_secret() -> None:
    payload = b'{"foo":"bar"}'
    signature = sign_payload(payload, "secret-a" * 4)
    assert verify_signature(payload, signature, "secret-b" * 4) is False
