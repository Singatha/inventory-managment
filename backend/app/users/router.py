from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_roles
from app.core.database import get_session
from app.users.models import User, UserRole
from app.users.schemas import UserListResponse, UserResponse, UserUpdate
from app.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])
AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=UserListResponse, summary="List users")
async def list_users(
    _: AdminUser,
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UserListResponse:
    users, total = await UserService(session).list_users(page=page, page_size=page_size)
    return UserListResponse(items=users, total=total, page=page, page_size=page_size)


@router.get("/{user_id}", response_model=UserResponse, summary="Get a user")
async def get_user(user_id: int, _: AdminUser, session: Session) -> User:
    return await UserService(session).get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse, summary="Update a user")
async def update_user(
    user_id: int, changes: UserUpdate, actor: AdminUser, session: Session
) -> User:
    return await UserService(session).update_user(user_id, changes, actor)

