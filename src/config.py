from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379

    sql_endpoint: str = "sql_code"
    sql_max_requests: int = 5
    sql_window_seconds: int = 5

    python_endpoint: str = "python_code"
    python_max_requests: int = 3
    python_window_seconds: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RATE_LIMITER_",
        case_sensitive=False,
    )


@lru_cache
def get_config() -> Config:
    return Config()
