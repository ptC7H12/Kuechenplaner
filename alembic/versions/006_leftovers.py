"""add leftovers table

Tracks what was left over after a meal, either per recipe or per ingredient,
for statistics across multiple camps.

Revision ID: 006
Revises: 005
Create Date: 2026-05-15

"""
from alembic import op
import sqlalchemy as sa


revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "leftovers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("camp_id", sa.Integer(), nullable=False),
        sa.Column("meal_plan_id", sa.Integer(), nullable=True),
        sa.Column("recipe_id", sa.Integer(), nullable=True),
        sa.Column("ingredient_id", sa.Integer(), nullable=True),
        sa.Column("tracking_type", sa.String(length=20), nullable=False),
        sa.Column("percentage_left", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["camp_id"], ["camps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["meal_plan_id"], ["meal_plans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leftovers_id", "leftovers", ["id"])
    op.create_index("ix_leftovers_camp_id", "leftovers", ["camp_id"])
    op.create_index("ix_leftovers_recipe_id", "leftovers", ["recipe_id"])
    op.create_index("ix_leftovers_meal_plan_id", "leftovers", ["meal_plan_id"])


def downgrade() -> None:
    op.drop_index("ix_leftovers_meal_plan_id", table_name="leftovers")
    op.drop_index("ix_leftovers_recipe_id", table_name="leftovers")
    op.drop_index("ix_leftovers_camp_id", table_name="leftovers")
    op.drop_index("ix_leftovers_id", table_name="leftovers")
    op.drop_table("leftovers")
