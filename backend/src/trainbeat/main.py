from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import auth as auth_api
from .api import groups as groups_api
from .api import health as health_api
from .api import me as me_api
from .api import sessions as sessions_api
from .api import webhook as webhook_api
from .api import workouts as workouts_api
from .config import settings
from .middleware import TelegramAuthMiddleware

app = FastAPI(title="TrainBeat API", version="0.0.1")
app.add_middleware(TelegramAuthMiddleware)
app.include_router(health_api.router)
app.include_router(webhook_api.router)
app.include_router(auth_api.router)
app.include_router(me_api.router)
app.include_router(groups_api.router)
app.include_router(workouts_api.exercises_router)
app.include_router(workouts_api.workouts_router)
app.include_router(sessions_api.router)


def _mount_mini_app() -> None:
    dist = Path(settings.mini_app_dist)
    if not dist.is_absolute():
        # Resolve relative to repo root (backend's parent).
        dist = (Path(__file__).resolve().parents[3] / dist).resolve()
    assets = dist / "assets"
    index = dist / "index.html"
    if not index.exists():
        return
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/", include_in_schema=False)
    async def root() -> FileResponse:
        return FileResponse(str(index))


_mount_mini_app()
