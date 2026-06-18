import asyncio
import logging
import sys

import uvicorn
from aiogram import Bot
from pythonjsonlogger.json import JsonFormatter

from .bot import dp, start_bot
from .config import settings
from .main import app
from .scheduler import build_scheduler
from .telegram_sender import make_telegram_sender


def _configure_logging() -> None:
    handler = logging.StreamHandler()
    if settings.app_env == "dev":
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    else:
        handler.setFormatter(
            JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


async def _serve_polling() -> None:
    """Long-poll Telegram + serve HTTP + run scheduler."""
    bot = Bot(settings.telegram_bot_token)
    app.state.bot = bot
    scheduler = build_scheduler(make_telegram_sender(bot))
    scheduler.start()
    try:
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await asyncio.gather(server.serve(), start_bot())
    finally:
        scheduler.shutdown(wait=False)


async def _serve_webhook() -> None:
    """Webhook-driven bot + serve HTTP + run scheduler (opt-in via BOT_MODE)."""
    bot = Bot(settings.telegram_bot_token)
    app.state.bot = bot
    scheduler = build_scheduler(make_telegram_sender(bot))
    scheduler.start()
    try:
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


def _serve() -> None:
    _configure_logging()
    if settings.bot_mode == "webhook":
        asyncio.run(_serve_webhook())
    else:
        asyncio.run(_serve_polling())


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] == "serve":
        _serve()
        return 0
    print(f"unknown subcommand: {args[0]}", file=sys.stderr)
    return 1


# Make Dispatcher importable from this module for parity with PRD-01 layout.
__all__ = ["app", "dp", "main"]


if __name__ == "__main__":
    sys.exit(main())
