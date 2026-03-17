from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://conquer:conquer@db:5432/conquer"

    # JWT
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"

    # App
    debug: bool = False
    project_name: str = "Conquer v5"


settings = Settings()
