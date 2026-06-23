"""add media columns to exercises

Revision ID: 0008_exercise_media
Revises: 0007_notifications
Create Date: 2026-06-23

"""

import sqlalchemy as sa

from alembic import op

revision: str = "0008_exercise_media"
down_revision: str | None = "0007_notifications"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("exercises", sa.Column("media_type", sa.String(length=16), nullable=True))
    op.add_column("exercises", sa.Column("media_file_id", sa.String(length=256), nullable=True))
    op.add_column(
        "exercises", sa.Column("media_file_unique_id", sa.String(length=128), nullable=True)
    )
    op.add_column("exercises", sa.Column("media_message_id", sa.BigInteger(), nullable=True))
    op.add_column("exercises", sa.Column("media_mime", sa.String(length=128), nullable=True))
    op.add_column("exercises", sa.Column("media_url", sa.String(length=1024), nullable=True))
    op.create_index(
        "ix_exercises_media_file_unique_id", "exercises", ["media_file_unique_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_exercises_media_file_unique_id", table_name="exercises")
    op.drop_column("exercises", "media_url")
    op.drop_column("exercises", "media_mime")
    op.drop_column("exercises", "media_message_id")
    op.drop_column("exercises", "media_file_unique_id")
    op.drop_column("exercises", "media_file_id")
    op.drop_column("exercises", "media_type")
