from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User, UserRole


async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    return await session.scalar(stmt)


async def count_users(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(User)) or 0


async def create(
    session: AsyncSession, *, telegram_id: int, name: str, role: UserRole
) -> User:
    user = User(telegram_id=telegram_id, name=name, role=role)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
