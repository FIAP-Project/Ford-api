from ford_shared.security.passwords import hash_password, verify_password


def test_hash_is_not_plaintext() -> None:
    h = hash_password("Strong#Pass123!")
    assert h != "Strong#Pass123!"
    assert h.startswith("$2") or h.startswith("$argon2")


def test_verify_correct_password() -> None:
    h = hash_password("Strong#Pass123!")
    assert verify_password("Strong#Pass123!", h) is True


def test_verify_wrong_password() -> None:
    h = hash_password("Strong#Pass123!")
    assert verify_password("wrong", h) is False


def test_two_hashes_are_different_for_same_password() -> None:
    a = hash_password("Strong#Pass123!")
    b = hash_password("Strong#Pass123!")
    assert a != b
