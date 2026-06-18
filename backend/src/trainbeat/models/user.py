import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, String, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserRole(enum.StrEnum):
    trainer = "trainer"
    athlete = "athlete"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
