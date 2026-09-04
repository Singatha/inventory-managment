import pytest

from app.auth.dependencies import require_roles
from app.common.errors import AppError
from app.users.models import User, UserRole


def make_user(role: UserRole) -> User:
    user = User(
        email="user@example.com",
        password_hash="unused",
        first_name="Test",
        last_name="User",
        role=role,
    )
    user.id = 1
    return user


@pytest.mark.asyncio
async def test_role_guard_allows_an_authorized_user() -> None:
    guard = require_roles(UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER)
    user = make_user(UserRole.ADMIN)

    assert await guard(current_user=user) is user


@pytest.mark.asyncio
async def test_role_guard_rejects_an_unauthorized_user() -> None:
    guard = require_roles(UserRole.ADMIN)

    with pytest.raises(AppError) as error:
        await guard(current_user=make_user(UserRole.EMPLOYEE))

    assert error.value.status_code == 403
    assert error.value.code == "INSUFFICIENT_PERMISSIONS"
