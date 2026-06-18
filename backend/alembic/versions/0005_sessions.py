"""create sessions table

Revision ID: 0005_sessions
Revises: 0004_workouts
Create Date: 2026-06-18

"""

import sqlalchemy as sa

from alembic import op

revision: str = "0005_sessions"
down_revision: str | None = "0004_workouts"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "group_id",
            sa.Integer(),
            sa.ForeignKey("groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workout_template_id",
            sa.Integer(),
            sa.ForeignKey("workout_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("recurrence_rule", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.Enum("scheduled", "completed", "cancelled", name="session_status"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_sessions_group_id", "sessions", ["group_id"])
    op.create_index("ix_sessions_scheduled_at", "sessions", ["scheduled_at"])


def downgrade() -> None:
    op.drop_index("ix_sessions_scheduled_at", table_name="sessions")
    op.drop_index("ix_sessions_group_id", table_name="sessions")
    op.drop_table("sessions")
    sa.Enum(name="session_status").drop(op.get_bind())
