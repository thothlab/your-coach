import logging
from collections.abc import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import settings
from .db import SessionLocal
from .repositories import notification as notification_repo

logger = logging.getLogger(__name__)


def build_scheduler(sender: Callable[[int, str], Awaitable[None]]) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    async def tick() -> None:
        async with SessionLocal() as session:
            try:
                delivered = await notification_repo.deliver_due(session, sender=sender)
            except Exception:  # noqa: BLE001 — log and continue
                logger.exception("notification sweep failed")
                return
        if delivered:
            logger.info("notification sweep delivered %d row(s)", delivered)

    scheduler.add_job(
        tick,
        "interval",
        minutes=settings.scheduler_interval_minutes,
        coalesce=True,
        max_instances=1,
        id="notification_sweep",
    )
    return scheduler
