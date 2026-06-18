from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness — no external dependencies."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JSONResponse:
    """Readiness — confirms DB reachability with a trivial query."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — surface any DB error
        return JSONResponse(
            {"status": "unavailable", "component": "database", "error": str(exc)[:200]},
            status_code=503,
        )
    return JSONResponse({"status": "ok"})
