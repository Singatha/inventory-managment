import asyncio

import structlog

from app.auth.security import hash_password
from app.core.config import get_settings
from app.core.database import async_session_factory, engine
from app.users.models import User, UserRole
from app.users.repository import UserRepository

logger = structlog.get_logger()


async def bootstrap_admin() -> None:
    settings = get_settings()
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return

    async with async_session_factory() as session:
        repository = UserRepository(session)
        existing = await repository.get_by_email(settings.bootstrap_admin_email)
        if existing is not None:
            return
        repository.add(
            User(
                email=settings.bootstrap_admin_email.lower(),
                password_hash=hash_password(settings.bootstrap_admin_password),
                first_name=settings.bootstrap_admin_first_name,
                last_name=settings.bootstrap_admin_last_name,
                role=UserRole.ADMIN,
            )
        )
        await session.commit()
        logger.info("bootstrap_admin_created", email=settings.bootstrap_admin_email.lower())


async def main() -> None:
    try:
        await bootstrap_admin()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

