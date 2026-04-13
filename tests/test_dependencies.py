from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.api.dependencies import rate_limiter_factory


class StubRateLimiter:
    def __init__(self, responses: list[bool], should_fail: bool = False) -> None:
        self._responses = responses
        self._should_fail = should_fail

    async def is_limited(
        self,
        ip_address: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        if self._should_fail:
            raise RuntimeError("Redis operation failed.")
        return self._responses.pop(0)


def _build_request(ip: str = "127.0.0.1") -> SimpleNamespace:
    return SimpleNamespace(client=SimpleNamespace(host=ip))


@pytest.mark.asyncio
async def test_dependency_allows_request_when_not_limited() -> None:
    dependency = rate_limiter_factory("sql_code", 5, 5)
    await dependency(_build_request(), StubRateLimiter([False]))


@pytest.mark.asyncio
async def test_dependency_raises_429_when_limited() -> None:
    dependency = rate_limiter_factory("sql_code", 5, 5)

    with pytest.raises(HTTPException) as error_info:
        await dependency(_build_request(), StubRateLimiter([True]))

    assert error_info.value.status_code == 429


@pytest.mark.asyncio
async def test_dependency_raises_503_when_storage_unavailable() -> None:
    dependency = rate_limiter_factory("sql_code", 5, 5)

    with pytest.raises(HTTPException) as error_info:
        await dependency(_build_request(), StubRateLimiter([], should_fail=True))

    assert error_info.value.status_code == 503
