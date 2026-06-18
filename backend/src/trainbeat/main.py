from fastapi import FastAPI

from .config import settings

app = FastAPI(title="TrainBeat API", version="0.0.1")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
