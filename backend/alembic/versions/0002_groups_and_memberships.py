"""create groups and memberships tables

Revision ID: 0002_groups_and_memberships
Revises: 0001_users
Create Date: 2026-06-18

"""

import sqlalchemy as sa

from alembic import op

revision: str = "0002_groups_and_memberships"
down_revision: str | None = "0001_users"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "trainer_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "type",
            sa.Enum("group", "personal", name="group_type"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_groups_trainer_id", "groups", ["trainer_id"])

    op.create_table(
        "memberships",
        sa.Column(
            "group_id",
            sa.Integer(),
            sa.ForeignKey("groups.id", ondelete="CASCADE"),
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
            sa.Enum("pending", "active", "removed", name="membership_status"),
            nullable=False,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_memberships_athlete_id", "memberships", ["athlete_id"])


def downgrade() -> None:
    op.drop_index("ix_memberships_athlete_id", table_name="memberships")
    op.drop_table("memberships")
    op.drop_index("ix_groups_trainer_id", table_name="groups")
    op.drop_table("groups")
    sa.Enum(name="membership_status").drop(op.get_bind())
    sa.Enum(name="group_type").drop(op.get_bind())
