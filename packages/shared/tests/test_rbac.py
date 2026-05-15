from ford_shared.security.rbac import Role, role_at_least


def test_user_does_not_have_analyst() -> None:
    assert role_at_least(Role.USER, Role.ANALYST) is False


def test_analyst_has_user() -> None:
    assert role_at_least(Role.ANALYST, Role.USER) is True


def test_admin_has_everything() -> None:
    assert role_at_least(Role.ADMIN, Role.USER) is True
    assert role_at_least(Role.ADMIN, Role.ANALYST) is True
    assert role_at_least(Role.ADMIN, Role.ADMIN) is True


def test_user_has_self() -> None:
    assert role_at_least(Role.USER, Role.USER) is True
