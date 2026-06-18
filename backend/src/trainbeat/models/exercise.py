import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ExerciseUnit(enum.StrEnum):
    reps = "reps"
    seconds = "seconds"
    meters = "meters"
    kg = "kg"


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[ExerciseUnit] = mapped_column(
        Enum(ExerciseUnit, name="exercise_unit"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
