"""create exercises, workout templates and items

Revision ID: 0004_workouts
Revises: 0003_invites
Create Date: 2026-06-18

"""

import sqlalchemy as sa

from alembic import op

revision: str = "0004_workouts"
down_revision: str | None = "0003_invites"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "exercises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "trainer_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "unit",
            sa.Enum("reps", "seconds", "meters", "kg", name="exercise_unit"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_exercises_trainer_id", "exercises", ["trainer_id"])

    op.create_table(
        "workout_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "trainer_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_workout_templates_trainer_id", "workout_templates", ["trainer_id"])

    op.create_table(
        "workout_template_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "template_id",
            sa.Integer(),
            sa.ForeignKey("workout_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercises.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("target_reps", sa.Integer(), nullable=True),
        sa.Column("target_weight", sa.Numeric(6, 2), nullable=True),
        sa.Column("target_seconds", sa.Integer(), nullable=True),
        sa.UniqueConstraint("template_id", "position", name="uq_template_position"),
    )
    op.create_index(
        "ix_workout_template_items_template_id",
        "workout_template_items",
        ["template_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workout_template_items_template_id", table_name="workout_template_items"
    )
    op.drop_table("workout_template_items")
    op.drop_index("ix_workout_templates_trainer_id", table_name="workout_templates")
    op.drop_table("workout_templates")
    op.drop_index("ix_exercises_trainer_id", table_name="exercises")
    op.drop_table("exercises")
    sa.Enum(name="exercise_unit").drop(op.get_bind())
