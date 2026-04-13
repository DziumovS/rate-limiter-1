from collections.abc import Callable

import pytest

from src.services.rate_limiter import RateLimiter


class FakePipeline:
    def __init__(self, storage: dict[str, dict[str, float]]) -> None:
        self.storage = storage
        self.operations: list[tuple[str, tuple[object, ...]]] = []

    async def __aenter__(self) -> "FakePipeline":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> None:
        self.operations.append(("zremrangebyscore", (key, min_score, max_score)))

    async def zcard(self, key: str) -> None:
        self.operations.append(("zcard", (key,)))

    async def zadd(self, key: str, value: dict[str, float]) -> None:
        self.operations.append(("zadd", (key, value)))

    async def expire(self, key: str, seconds: int) -> None:
        self.operations.append(("expire", (key, seconds)))

    async def execute(self) -> list[object]:
        results: list[object] = []
        for operation, args in self.operations:
            if operation == "zremrangebyscore":
                key, min_score, max_score = args
                bucket = self.storage.setdefault(key, {})
                removable = [member for member, score in bucket.items() if min_score <= score <= max_score]
                for member in removable:
                    del bucket[member]
                results.append(len(removable))
            elif operation == "zcard":
                (key,) = args
                bucket = self.storage.setdefault(key, {})
                results.append(len(bucket))
            elif operation == "zadd":
                key, payload = args
                bucket = self.storage.setdefault(key, {})
                bucket.update(payload)
                results.append(len(payload))
            elif operation == "expire":
                results.append(True)
        self.operations.clear()
        return results


class FakeRedis:
    def __init__(self) -> None:
        self.storage: dict[str, dict[str, float]] = {}

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self.storage)


def _time_provider_factory(values: list[float]) -> Callable[[], float]:
    iterator = iter(values)
    return lambda: next(iterator)


def _request_id_provider_factory(values: list[str]) -> Callable[[], str]:
    iterator = iter(values)
    return lambda: next(iterator)


@pytest.mark.asyncio
async def test_rate_limiter_blocks_when_limit_reached() -> None:
    redis = FakeRedis()
    time_provider = _time_provider_factory([1.0, 1.0, 1.0, 1.0])
    request_id_provider = _request_id_provider_factory(["req-1", "req-2", "req-3"])
    limiter = RateLimiter(redis=redis, time_provider=time_provider, request_id_provider=request_id_provider)

    assert await limiter.is_limited("127.0.0.1", "sql_code", max_requests=2, window_seconds=5) is False
    assert await limiter.is_limited("127.0.0.1", "sql_code", max_requests=2, window_seconds=5) is False
    assert await limiter.is_limited("127.0.0.1", "sql_code", max_requests=2, window_seconds=5) is True


@pytest.mark.asyncio
async def test_rate_limiter_allows_after_window_expires() -> None:
    redis = FakeRedis()
    time_provider = _time_provider_factory([1.0, 1.0, 7.5, 7.5])
    request_id_provider = _request_id_provider_factory(["req-1", "req-2", "req-3"])
    limiter = RateLimiter(redis=redis, time_provider=time_provider, request_id_provider=request_id_provider)

    assert await limiter.is_limited("127.0.0.1", "python_code", max_requests=1, window_seconds=5) is False
    assert await limiter.is_limited("127.0.0.1", "python_code", max_requests=1, window_seconds=5) is True
    assert await limiter.is_limited("127.0.0.1", "python_code", max_requests=1, window_seconds=5) is False
