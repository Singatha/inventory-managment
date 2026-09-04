from functools import lru_cache
from typing import Annotated

from pydantic import EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "StockFlow API"
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://stockflow:stockflow_dev_password@localhost:5432/stockflow"
    jwt_secret: str = Field(default="development-only-secret-change-me", min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    bootstrap_admin_email: EmailStr | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_first_name: str = "StockFlow"
    bootstrap_admin_last_name: str = "Admin"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
