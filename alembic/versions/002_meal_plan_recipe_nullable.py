"""make meal_plans.recipe_id nullable with ON DELETE SET NULL

SQLite doesn't support ALTER COLUMN, so we rebuild the table: create
a new one with the desired schema, copy rows, drop the old, rename.

Revision ID: 002
Revises: 001
Create Date: 2026-05-13

"""
from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def _create_meal_plans(name: str, *, recipe_id_nullable: bool, recipe_fk_on_delete: str | None) -> None:
    op.create_table(
        name,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("camp_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=recipe_id_nullable),
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
        sa.ForeignKeyConstraint(
            ["recipe_id"], ["recipes.id"],
            ondelete=recipe_fk_on_delete,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "camp_id", "meal_date", "meal_type", "position",
            name="uix_meal_plan_position",
        ),
    )


def _create_meal_plan_indexes(table_name: str) -> None:
    op.create_index(f"ix_{table_name}_id", table_name, ["id"])
    op.create_index(f"ix_{table_name}_camp_id", table_name, ["camp_id"])
    op.create_index(f"ix_{table_name}_recipe_id", table_name, ["recipe_id"])
    op.create_index(f"ix_{table_name}_meal_date", table_name, ["meal_date"])
    op.create_index(f"ix_{table_name}_meal_type", table_name, ["meal_type"])


def upgrade() -> None:
    _create_meal_plans("meal_plans_new", recipe_id_nullable=True, recipe_fk_on_delete="SET NULL")

    op.execute(
        """
        INSERT INTO meal_plans_new
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
    op.rename_table("meal_plans_new", "meal_plans")
    _create_meal_plan_indexes("meal_plans")


def downgrade() -> None:
    _create_meal_plans("meal_plans_old", recipe_id_nullable=False, recipe_fk_on_delete=None)

    op.execute(
        """
        INSERT INTO meal_plans_old
            (id, camp_id, recipe_id, meal_date, meal_type, position, notes, created_at, updated_at)
        SELECT id, camp_id, recipe_id, meal_date, meal_type, position, notes, created_at, updated_at
        FROM meal_plans
        WHERE recipe_id IS NOT NULL
        """
    )

    op.drop_index("ix_meal_plans_meal_type", table_name="meal_plans")
    op.drop_index("ix_meal_plans_meal_date", table_name="meal_plans")
    op.drop_index("ix_meal_plans_recipe_id", table_name="meal_plans")
    op.drop_index("ix_meal_plans_camp_id", table_name="meal_plans")
    op.drop_index("ix_meal_plans_id", table_name="meal_plans")
    op.drop_table("meal_plans")
    op.rename_table("meal_plans_old", "meal_plans")
    _create_meal_plan_indexes("meal_plans")
