from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False
    )
    set_index: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_weight: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    actual_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        UniqueConstraint(
            "session_id", "athlete_id", "exercise_id", "set_index",
            name="uq_workout_log_set",
        ),
    )
