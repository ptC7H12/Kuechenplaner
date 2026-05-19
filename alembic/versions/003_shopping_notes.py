"""add ingredient.note and shopping_list_notes table

Adds:
- ingredients.note (Text, nullable) for global per-ingredient notes
- shopping_list_notes table for camp-specific notes per (camp_id, ingredient_id)

SQLite doesn't support ALTER COLUMN, but adding a nullable column is fine.

Revision ID: 003
Revises: 002
Create Date: 2026-05-15

"""
from alembic import op
import sqlalchemy as sa


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ingredients",
        sa.Column("note", sa.Text(), nullable=True),
    )

    op.create_table(
        "shopping_list_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("camp_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["camp_id"], ["camps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("camp_id", "ingredient_id", name="uix_shopping_note_camp_ingredient"),
    )
    op.create_index("ix_shopping_list_notes_id", "shopping_list_notes", ["id"])
    op.create_index("ix_shopping_list_notes_camp_id", "shopping_list_notes", ["camp_id"])
    op.create_index("ix_shopping_list_notes_ingredient_id", "shopping_list_notes", ["ingredient_id"])


def downgrade() -> None:
    op.drop_index("ix_shopping_list_notes_ingredient_id", table_name="shopping_list_notes")
    op.drop_index("ix_shopping_list_notes_camp_id", table_name="shopping_list_notes")
    op.drop_index("ix_shopping_list_notes_id", table_name="shopping_list_notes")
    op.drop_table("shopping_list_notes")

    # SQLite rebuild for drop column
    op.create_table(
        "ingredients_old",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.execute(
        """
        INSERT INTO ingredients_old (id, name, unit, category, created_at, updated_at)
        SELECT id, name, unit, category, created_at, updated_at FROM ingredients
        """
    )
    op.drop_index("ix_ingredients_name", table_name="ingredients")
    op.drop_index("ix_ingredients_category", table_name="ingredients")
    op.drop_index("ix_ingredients_id", table_name="ingredients")
    op.drop_table("ingredients")
    op.rename_table("ingredients_old", "ingredients")
    op.create_index("ix_ingredients_id", "ingredients", ["id"])
    op.create_index("ix_ingredients_name", "ingredients", ["name"], unique=True)
    op.create_index("ix_ingredients_category", "ingredients", ["category"])
