from collections.abc import Awaitable, Callable
from typing import Annotated

import jwt
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import TokenClaims
from app.auth.security import decode_token
from app.common.errors import AppError
from app.core.database import get_session
from app.users.models import User, UserRole
from app.users.repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    unauthorized = AppError(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="NOT_AUTHENTICATED",
        message="A valid access token is required.",
    )
    if credentials is None:
        raise unauthorized
    try:
        claims = TokenClaims.model_validate(decode_token(credentials.credentials))
        if claims.type != "access":
            raise ValueError("Wrong token type")
        user_id = int(claims.sub)
    except (jwt.PyJWTError, ValueError) as exc:
        raise unauthorized from exc

    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


def require_roles(*roles: UserRole) -> Callable[..., Awaitable[User]]:
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in roles:
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                code="INSUFFICIENT_PERMISSIONS",
                message="You do not have permission to perform this action.",
                details={"required_roles": [role.value for role in roles]},
            )
        return current_user

    return role_checker
