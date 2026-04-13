from collections.abc import Awaitable, Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from src.redis_client import get_redis
from src.services.rate_limiter import RateLimiter


@lru_cache
def get_rate_limiter() -> RateLimiter:
    return RateLimiter(get_redis())


def rate_limiter_factory(
    endpoint: str,
    max_requests: int,
    window_seconds: int,
) -> Callable[[Request, Annotated[RateLimiter, Depends(get_rate_limiter)]], Awaitable[None]]:

    async def dependency(
        request: Request,
        rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    ) -> None:
        ip_address = request.client.host if request.client else "unknown"
        try:
            is_limited = await rate_limiter.is_limited(
                ip_address=ip_address,
                endpoint=endpoint,
                max_requests=max_requests,
                window_seconds=window_seconds,
            )
        except RuntimeError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limiter storage unavailable.",
            ) from error

        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests.",
            )

    return dependency
