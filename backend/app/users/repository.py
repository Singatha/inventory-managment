from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return cast(User | None, await self.session.scalar(statement))

    async def list(self, *, offset: int, limit: int) -> tuple[list[User], int]:
        statement = select(User).order_by(User.created_at).offset(offset).limit(limit)
        users = list((await self.session.scalars(statement)).all())
        total = await self.session.scalar(select(func.count()).select_from(User))
        return users, total or 0

    def add(self, user: User) -> None:
        self.session.add(user)
