from fastapi import HTTPException, Request

from ..models import User


def current_user(request: Request) -> User:
    user: User | None = getattr(request.state, "current_user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="not authenticated")
    return user
