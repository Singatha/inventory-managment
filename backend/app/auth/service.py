import jwt
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, RegisterRequest, TokenClaims, TokenPair
from app.auth.security import create_token, decode_token, hash_password, verify_password
from app.common.errors import AppError
from app.core.config import get_settings
from app.users.models import User, UserRole
from app.users.repository import UserRepository

DUMMY_PASSWORD_HASH = hash_password("stockflow-dummy-password")


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)

    async def register(self, data: RegisterRequest) -> User:
        user = User(
            email=str(data.email).lower(),
            password_hash=hash_password(data.password),
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            role=UserRole.EMPLOYEE,
        )
        self.repository.add(user)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="EMAIL_ALREADY_REGISTERED",
                message="An account with this email address already exists.",
            ) from exc
        await self.session.refresh(user)
        return user

    async def login(self, data: LoginRequest) -> TokenPair:
        user = await self.repository.get_by_email(str(data.email).lower())
        if user is None:
            verify_password(data.password, DUMMY_PASSWORD_HASH)
        if user is None or not verify_password(data.password, user.password_hash):
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_CREDENTIALS",
                message="The email address or password is incorrect.",
            )
        if not user.is_active:
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                code="ACCOUNT_INACTIVE",
                message="This account has been deactivated.",
            )
        return self._token_pair(user)

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            claims = TokenClaims.model_validate(decode_token(refresh_token))
            if claims.type != "refresh":
                raise ValueError("Wrong token type")
            user_id = int(claims.sub)
        except (jwt.PyJWTError, ValueError) as exc:
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_REFRESH_TOKEN",
                message="The refresh token is invalid or has expired.",
            ) from exc

        user = await self.repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_REFRESH_TOKEN",
                message="The refresh token is invalid or has expired.",
            )
        return self._token_pair(user)

    def _token_pair(self, user: User) -> TokenPair:
        settings = get_settings()
        return TokenPair(
            access_token=create_token(user, "access"),
            refresh_token=create_token(user, "refresh"),
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=user,
        )
