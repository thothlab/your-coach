"""create attendance and workout_logs tables

Revision ID: 0006_attendance_and_logs
Revises: 0005_sessions
Create Date: 2026-06-18

"""

import sqlalchemy as sa

from alembic import op

revision: str = "0006_attendance_and_logs"
down_revision: str | None = "0005_sessions"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "attendance",
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "athlete_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "confirmed", "declined", "present", "absent",
                name="attendance_status",
            ),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_attendance_athlete_id", "attendance", ["athlete_id"])

    op.create_table(
        "workout_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "athlete_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercises.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("set_index", sa.Integer(), nullable=False),
        sa.Column("actual_reps", sa.Integer(), nullable=True),
        sa.Column("actual_weight", sa.Numeric(6, 2), nullable=True),
        sa.Column("actual_seconds", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "session_id", "athlete_id", "exercise_id", "set_index",
            name="uq_workout_log_set",
        ),
    )
    op.create_index(
        "ix_workout_logs_session_athlete",
        "workout_logs",
        ["session_id", "athlete_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_workout_logs_session_athlete", table_name="workout_logs")
    op.drop_table("workout_logs")
    op.drop_index("ix_attendance_athlete_id", table_name="attendance")
    op.drop_table("attendance")
    sa.Enum(name="attendance_status").drop(op.get_bind())
