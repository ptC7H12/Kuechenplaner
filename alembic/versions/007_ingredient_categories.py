"""replace ingredient.category string with categories table + FK

Introduces a first-class ``categories`` table (id, name, color) and replaces
the free-text ``ingredients.category`` column with a nullable
``ingredients.category_id`` foreign key.

Data migration: every distinct non-empty ``ingredients.category`` string
becomes a ``categories`` row; existing ingredients are re-pointed via
``category_id``. The old string column is then dropped.

SQLite has no ALTER COLUMN / DROP COLUMN with FK in place, so the column
add/drop runs through ``batch_alter_table`` (table rebuild).

Revision ID: 007
Revises: 006
Create Date: 2026-06-08

"""
import sqlalchemy as sa
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_id", "categories", ["id"])
    op.create_index("ix_categories_name", "categories", ["name"], unique=True)

    # Seed categories from the distinct existing ingredient category strings.
    op.execute(
        """
        INSERT INTO categories (name, color, created_at, updated_at)
        SELECT DISTINCT TRIM(category), '#6B7280', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM ingredients
        WHERE category IS NOT NULL AND TRIM(category) != ''
        """
    )

    # Add the FK column (table rebuild via batch mode for SQLite).
    with op.batch_alter_table("ingredients") as batch_op:
        batch_op.add_column(sa.Column("category_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_ingredients_category_id",
            "categories",
            ["category_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # Re-point ingredients at their category row.
    op.execute(
        """
        UPDATE ingredients
        SET category_id = (
            SELECT c.id FROM categories c WHERE c.name = TRIM(ingredients.category)
        )
        WHERE category IS NOT NULL AND TRIM(category) != ''
        """
    )

    # Drop the old string column and its index.
    with op.batch_alter_table("ingredients") as batch_op:
        batch_op.drop_index("ix_ingredients_category")
        batch_op.drop_column("category")

    op.create_index("ix_ingredients_category_id", "ingredients", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_ingredients_category_id", table_name="ingredients")

    # Re-add the string column.
    with op.batch_alter_table("ingredients") as batch_op:
        batch_op.add_column(sa.Column("category", sa.String(length=100), nullable=True))

    # Restore the string values from the categories table.
    op.execute(
        """
        UPDATE ingredients
        SET category = (
            SELECT c.name FROM categories c WHERE c.id = ingredients.category_id
        )
        WHERE category_id IS NOT NULL
        """
    )
    op.execute("UPDATE ingredients SET category = 'Sonstiges' WHERE category IS NULL")

    with op.batch_alter_table("ingredients") as batch_op:
        batch_op.drop_constraint("fk_ingredients_category_id", type_="foreignkey")
        batch_op.drop_column("category_id")

    op.create_index("ix_ingredients_category", "ingredients", ["category"])

    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_index("ix_categories_id", table_name="categories")
    op.drop_table("categories")
