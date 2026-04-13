from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from redis.exceptions import RedisError

from src.api.routes.code import router as code_router
from src.redis_client import get_redis


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    redis = get_redis()
    try:
        await redis.ping()
        print("Redis is available.")
    except RedisError as error:
        raise RuntimeError("Cannot connect to Redis.") from error

    try:
        yield
    finally:
        await redis.aclose()
        print("Redis connection closed.")


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(code_router)
    return app


app = create_app()
