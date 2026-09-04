from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)

    async def list_users(self, *, page: int, page_size: int) -> tuple[list[User], int]:
        return await self.repository.list(offset=(page - 1) * page_size, limit=page_size)

    async def get_user(self, user_id: int) -> User:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="USER_NOT_FOUND",
                message="The requested user does not exist.",
            )
        return user

    async def update_user(self, user_id: int, changes: UserUpdate, actor: User) -> User:
        user = await self.get_user(user_id)
        if user.id == actor.id and changes.is_active is False:
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="CANNOT_DEACTIVATE_SELF",
                message="You cannot deactivate your own account.",
            )
        if user.id == actor.id and changes.role is not None and changes.role != actor.role:
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="CANNOT_CHANGE_OWN_ROLE",
                message="You cannot change your own role.",
            )

        for field, value in changes.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

