import asyncio
import logging

import uvicorn

from .bot import start_bot
from .main import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


async def serve_http() -> None:
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    await asyncio.gather(serve_http(), start_bot())


if __name__ == "__main__":
    asyncio.run(main())
