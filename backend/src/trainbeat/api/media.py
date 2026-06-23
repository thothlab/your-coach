"""Exercise media: upload to Telegram (blob store), serve back, attach links.

Photos/videos are sent into a private storage channel; we keep their Telegram
file ids in Postgres. Photos (≤10 MB, always ≤20 MB) are streamed back through a
proxy (getFile is capped at 20 MB on the cloud Bot API). Videos can exceed that
download cap, so they are delivered by re-sending into the user's chat by
file_id instead.
"""

import io
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..bot_instance import get_bot
from ..config import settings
from ..db import get_session
from ..models import User
from ..repositories import exercise as exercise_repo
from .deps import current_user, trainer_from_init_data

# Routes under /api are covered by TelegramAuthMiddleware.
router = APIRouter(prefix="/api/exercises", tags=["media"])
# Public routes (outside /api): the <img> proxy can't send an auth header, and
# the multipart upload sidesteps BaseHTTPMiddleware's body handling.
public_router = APIRouter(tags=["media"])

PHOTO_MAX = 10 * 1024 * 1024
VIDEO_MAX = 50 * 1024 * 1024


class MediaInfo(BaseModel):
    media_type: str | None
    media_url: str | None
    media_file_unique_id: str | None


class LinkRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=1024)


def _media_info(ex) -> MediaInfo:
    return MediaInfo(
        media_type=ex.media_type,
        media_url=ex.media_url,
        media_file_unique_id=ex.media_file_unique_id,
    )


@public_router.post("/media/exercise/{exercise_id}", response_model=MediaInfo)
async def upload_media(
    exercise_id: int,
    file: UploadFile,
    trainer: Annotated[User, Depends(trainer_from_init_data)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MediaInfo:
    if settings.storage_channel_id is None:
        raise HTTPException(status_code=503, detail="media storage not configured")
    ex = await exercise_repo.get_owned(
        session, exercise_id=exercise_id, trainer_id=trainer.id
    )
    if ex is None:
        raise HTTPException(status_code=404, detail="exercise not found")

    data = await file.read()
    content_type = file.content_type or ""
    bot = get_bot()
    from aiogram.types import BufferedInputFile

    if content_type.startswith("image/"):
        if len(data) > PHOTO_MAX:
            raise HTTPException(status_code=413, detail="photo exceeds 10 MB")
        msg = await bot.send_photo(
            settings.storage_channel_id,
            BufferedInputFile(data, filename=file.filename or "photo"),
            caption=f"#exercise:{ex.id}",
        )
        media = msg.photo[-1]
        media_type = "photo"
    elif content_type.startswith("video/"):
        if len(data) > VIDEO_MAX:
            raise HTTPException(status_code=413, detail="video exceeds 50 MB")
        msg = await bot.send_video(
            settings.storage_channel_id,
            BufferedInputFile(data, filename=file.filename or "video"),
            caption=f"#exercise:{ex.id}",
        )
        media = msg.video
        media_type = "video"
    else:
        raise HTTPException(status_code=415, detail="only image/* or video/* allowed")

    ex.media_type = media_type
    ex.media_file_id = media.file_id
    ex.media_file_unique_id = media.file_unique_id
    ex.media_message_id = msg.message_id
    ex.media_mime = content_type
    ex.media_url = None
    await session.commit()
    await session.refresh(ex)
    return _media_info(ex)


@public_router.get("/media/file/{file_unique_id}")
async def serve_media(
    file_unique_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StreamingResponse:
    ex = await exercise_repo.get_by_media_unique_id(session, file_unique_id)
    if ex is None or ex.media_type != "photo" or ex.media_file_id is None:
        raise HTTPException(status_code=404, detail="media not found")
    bot = get_bot()
    tg_file = await bot.get_file(ex.media_file_id)
    buf = io.BytesIO()
    await bot.download_file(tg_file.file_path, destination=buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type=ex.media_mime or "image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.post("/{exercise_id}/media/link", response_model=MediaInfo)
async def attach_link(
    exercise_id: int,
    body: LinkRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MediaInfo:
    ex = await exercise_repo.get_owned(
        session, exercise_id=exercise_id, trainer_id=user.id
    )
    if ex is None:
        raise HTTPException(status_code=404, detail="exercise not found")
    ex.media_type = "link"
    ex.media_url = body.url
    ex.media_file_id = None
    ex.media_file_unique_id = None
    ex.media_message_id = None
    ex.media_mime = None
    await session.commit()
    await session.refresh(ex)
    return _media_info(ex)


@router.delete("/{exercise_id}/media", response_model=MediaInfo)
async def clear_media(
    exercise_id: int,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MediaInfo:
    ex = await exercise_repo.get_owned(
        session, exercise_id=exercise_id, trainer_id=user.id
    )
    if ex is None:
        raise HTTPException(status_code=404, detail="exercise not found")
    ex.media_type = None
    ex.media_file_id = None
    ex.media_file_unique_id = None
    ex.media_message_id = None
    ex.media_mime = None
    ex.media_url = None
    await session.commit()
    await session.refresh(ex)
    return _media_info(ex)


@router.post("/{exercise_id}/media/send")
async def send_media_to_chat(
    exercise_id: int,
    request: Request,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, bool]:
    ex = await exercise_repo.get_owned(
        session, exercise_id=exercise_id, trainer_id=user.id
    )
    if ex is None or ex.media_file_id is None:
        raise HTTPException(status_code=404, detail="media not found")
    bot = get_bot()
    if ex.media_type == "video":
        await bot.send_video(user.telegram_id, ex.media_file_id)
    else:
        await bot.send_photo(user.telegram_id, ex.media_file_id)
    return {"ok": True}
