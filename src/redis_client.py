from functools import lru_cache

from redis.asyncio import Redis

from src.config import get_config


@lru_cache
def get_redis() -> Redis:
    config = get_config()
    return Redis(host=config.redis_host, port=config.redis_port, decode_responses=True)
