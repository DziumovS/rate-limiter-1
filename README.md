# Rate Limiter (FastAPI + Redis)

Simple API with a Redis-backed **sliding window** rate limiter.

It limits requests:
- per **IP address**
- per **endpoint**
- by **max requests** during a **window duration**

When the limit is reached, requests are rejected with HTTP `429` until enough time passes and old requests leave the window.

## Features

- Sliding window algorithm with Redis sorted sets.
- Separate limits for each endpoint.
- Clear project structure (`config`, `services`, `api`).
- Environment-based configuration with `pydantic-settings`.
- Error handling for Redis failures (`503` fallback).
- Unit tests with `pytest`.

## Configuration

Environment variables are loaded from `.env`:

```env
RATE_LIMITER_REDIS_HOST=localhost
RATE_LIMITER_REDIS_PORT=6379
RATE_LIMITER_SQL_ENDPOINT=sql_code
RATE_LIMITER_SQL_MAX_REQUESTS=5
RATE_LIMITER_SQL_WINDOW_SECONDS=5
RATE_LIMITER_PYTHON_ENDPOINT=python_code
RATE_LIMITER_PYTHON_MAX_REQUESTS=3
RATE_LIMITER_PYTHON_WINDOW_SECONDS=10
```

## Run Locally

1. Start Redis:
```bash
docker compose up -d
```

2. Install dependencies:
```bash
uv sync
```

3. Run API:
```bash
uv run uvicorn src.app:app --reload
```
