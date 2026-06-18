"""create users table

Revision ID: 0001_users
Revises:
Create Date: 2026-06-18

"""

import sqlalchemy as sa

from alembic import op

revision: str = "0001_users"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("trainer", "athlete", name="user_role"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
    sa.Enum(name="user_role").drop(op.get_bind())
