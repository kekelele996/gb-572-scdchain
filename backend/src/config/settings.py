"""Runtime configuration. Every value can be overridden by an env var of the same name."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    # --- database ---
    DB_NAME: str = "scdchain_db"
    DB_USER: str = "scdchain_user"
    DB_PASSWORD: str = "scdchain_pwd"
    DB_HOST: str = "db"
    DB_PORT: int = 5432

    # --- auth ---
    JWT_SECRET: str = "scdchain_dev_jwt_secret_change_me_0612"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8

    # --- infra ---
    REDIS_URL: str = "redis://redis:6379/0"

    # --- zipper / conflict semantics ---
    # A change first observed on day D takes effect on D+1 (nightly batch, next-day effective).
    OVERRIDE_EFFECTIVE_DATE: str = "2026-11-06"
    BUILD_MAX_CHAINS: int = 5000

    # --- limits ---
    RATE_WINDOW_SECONDS: int = 60
    RATE_WINDOW_MAX: int = 120

    # --- demo seed ---
    SEED_DEMO: bool = True

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
