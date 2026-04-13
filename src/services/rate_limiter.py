from time import time
from typing import Callable
from uuid import uuid4

from redis.asyncio import Redis
from redis.exceptions import RedisError


class RateLimiter:
    def __init__(
        self,
        redis: Redis,
        time_provider: Callable[[], float] | None = None,
        request_id_provider: Callable[[], str] | None = None,
    ) -> None:
        self._redis = redis
        self._time_provider = time_provider or time
        self._request_id_provider = request_id_provider or (lambda: uuid4().hex)

    async def is_limited(
        self,
        ip_address: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        key = self._build_key(endpoint=endpoint, ip_address=ip_address)
        current_ms = int(self._time_provider() * 1000)
        window_start_ms = current_ms - window_seconds * 1000

        try:
            async with self._redis.pipeline() as pipe:
                # Remove outdated requests from the Redis sorted set.
                await pipe.zremrangebyscore(key, 0, window_start_ms)

                # Count active requests currently stored in Redis.
                await pipe.zcard(key)

                # Execute cleanup + count in one network roundtrip.
                result = await pipe.execute()

            _, current_count = result
            if current_count >= max_requests:
                return True

            request_id = f"{current_ms}-{self._request_id_provider()}"

            async with self._redis.pipeline() as pipe:
                # Add current request timestamp to the Redis sorted set.
                await pipe.zadd(key, {request_id: current_ms})

                # Set Redis key expiration equal to limiter window duration.
                await pipe.expire(key, window_seconds)

                # Execute write operations and persist current request.
                await pipe.execute()

        except RedisError as error:
            raise RuntimeError("Redis operation failed.") from error

        return False

    @staticmethod
    def _build_key(endpoint: str, ip_address: str) -> str:
        return f"rate_limiter:{endpoint}:{ip_address}"
