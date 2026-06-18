import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, PrimaryKeyConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AttendanceStatus(enum.StrEnum):
    pending = "pending"
    confirmed = "confirmed"
    declined = "declined"
    present = "present"
    absent = "absent"


class Attendance(Base):
    __tablename__ = "attendance"

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, name="attendance_status"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (PrimaryKeyConstraint("session_id", "athlete_id"),)
