"""create notifications table

Revision ID: 0007_notifications
Revises: 0006_attendance_and_logs
Create Date: 2026-06-18

"""

import sqlalchemy as sa

from alembic import op

revision: str = "0007_notifications"
down_revision: str | None = "0006_attendance_and_logs"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "kind",
            sa.Enum("reminder", "broadcast", name="notification_kind"),
            nullable=False,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("scheduled", "sent", "cancelled", name="notification_status"),
            nullable=False,
        ),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.UniqueConstraint(
            "user_id", "session_id", "kind", "scheduled_at",
            name="uq_notification_dedup",
        ),
    )
    op.create_index(
        "ix_notifications_scheduled_at", "notifications", ["scheduled_at", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_scheduled_at", table_name="notifications")
    op.drop_table("notifications")
    sa.Enum(name="notification_kind").drop(op.get_bind())
    sa.Enum(name="notification_status").drop(op.get_bind())
