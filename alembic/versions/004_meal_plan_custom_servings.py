"""add meal_plans.custom_servings

Optional per-meal-plan override of camp.participant_count for recipe scaling.

Revision ID: 004
Revises: 003
Create Date: 2026-05-15

"""
from alembic import op
import sqlalchemy as sa


revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "meal_plans",
        sa.Column("custom_servings", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    # SQLite rebuild to drop a column.
    op.create_table(
        "meal_plans_old",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("camp_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=True),
        sa.Column("meal_date", sa.DateTime(), nullable=False),
        sa.Column(
            "meal_type",
            sa.Enum("BREAKFAST", "LUNCH", "DINNER", name="mealtype"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["camp_id"], ["camps.id"]),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "camp_id", "meal_date", "meal_type", "position",
            name="uix_meal_plan_position",
        ),
    )
    op.execute(
        """
        INSERT INTO meal_plans_old
            (id, camp_id, recipe_id, meal_date, meal_type, position, notes, created_at, updated_at)
        SELECT id, camp_id, recipe_id, meal_date, meal_type, position, notes, created_at, updated_at
        FROM meal_plans
        """
    )
    op.drop_index("ix_meal_plans_meal_type", table_name="meal_plans")
    op.drop_index("ix_meal_plans_meal_date", table_name="meal_plans")
    op.drop_index("ix_meal_plans_recipe_id", table_name="meal_plans")
    op.drop_index("ix_meal_plans_camp_id", table_name="meal_plans")
    op.drop_index("ix_meal_plans_id", table_name="meal_plans")
    op.drop_table("meal_plans")
    op.rename_table("meal_plans_old", "meal_plans")
    op.create_index("ix_meal_plans_id", "meal_plans", ["id"])
    op.create_index("ix_meal_plans_camp_id", "meal_plans", ["camp_id"])
    op.create_index("ix_meal_plans_recipe_id", "meal_plans", ["recipe_id"])
    op.create_index("ix_meal_plans_meal_date", "meal_plans", ["meal_date"])
    op.create_index("ix_meal_plans_meal_type", "meal_plans", ["meal_type"])
