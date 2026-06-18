from fastapi import FastAPI

from .api import auth as auth_api
from .api import groups as groups_api
from .api import me as me_api
from .api import workouts as workouts_api
from .config import settings
from .middleware import TelegramAuthMiddleware

app = FastAPI(title="TrainBeat API", version="0.0.1")
app.add_middleware(TelegramAuthMiddleware)
app.include_router(auth_api.router)
app.include_router(me_api.router)
app.include_router(groups_api.router)
app.include_router(workouts_api.exercises_router)
app.include_router(workouts_api.workouts_router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
