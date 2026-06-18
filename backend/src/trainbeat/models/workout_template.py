from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    items: Mapped[list["WorkoutTemplateItem"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="WorkoutTemplateItem.position",
        lazy="selectin",
    )


class WorkoutTemplateItem(Base):
    __tablename__ = "workout_template_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("workout_templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False
    )
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    target_reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_weight: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    target_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    template: Mapped[WorkoutTemplate] = relationship(back_populates="items")

    __table_args__ = (
        UniqueConstraint("template_id", "position", name="uq_template_position"),
    )
