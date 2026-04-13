from typing import Annotated

from fastapi import APIRouter, Body, Depends
from src.api.dependencies import rate_limiter_factory
from src.config import get_config

router = APIRouter()
settings = get_config()

sql_rate_limiter = rate_limiter_factory(
    endpoint=settings.sql_endpoint,
    max_requests=settings.sql_max_requests,
    window_seconds=settings.sql_window_seconds,
)

python_rate_limiter = rate_limiter_factory(
    endpoint=settings.python_endpoint,
    max_requests=settings.python_max_requests,
    window_seconds=settings.python_window_seconds,
)


@router.post("/sql_code", dependencies=[Depends(sql_rate_limiter)])
async def send_sql_code(code: Annotated[str, Body(embed=True)]) -> dict[str, bool]:
    return {"ok": True}


@router.post("/python_code", dependencies=[Depends(python_rate_limiter)])
async def send_python_code(code: Annotated[str, Body(embed=True)]) -> dict[str, bool]:
    return {"ok": True}
