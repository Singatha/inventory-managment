from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.auth.service import AuthService
from app.core.database import get_session
from app.users.models import User
from app.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register an employee account",
)
async def register(data: RegisterRequest, session: Session) -> User:
    return await AuthService(session).register(data)


@router.post("/login", response_model=TokenPair, summary="Sign in")
async def login(data: LoginRequest, session: Session) -> TokenPair:
    return await AuthService(session).login(data)


@router.post("/refresh", response_model=TokenPair, summary="Refresh an access token")
async def refresh(data: RefreshRequest, session: Session) -> TokenPair:
    return await AuthService(session).refresh(data.refresh_token)


@router.get("/me", response_model=UserResponse, summary="Get the current user")
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user

