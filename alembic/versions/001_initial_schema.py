"""initial schema baseline (pre-nullable meal_plans.recipe_id)

Baseline migration matching the schema produced by
Base.metadata.create_all() in v1.2.x. Note: recipe_id on meal_plans is
NOT NULL here — migration 002 relaxes it. This split lets legacy DBs
created before Alembic was wired up be stamped to "001" and then
upgraded forward to head, without DDL conflicts.

Revision ID: 001
Revises:
Create Date: 2026-05-13

"""
from alembic import op
import sqlalchemy as sa


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "camps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("participant_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("last_accessed", sa.DateTime(), nullable=True),
        sa.CheckConstraint("start_date <= end_date", name="check_camp_date_range"),
        sa.CheckConstraint("participant_count > 0", name="check_camp_participant_count_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_camps_id", "camps", ["id"])
    op.create_index("ix_camps_start_date", "camps", ["start_date"])

    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("base_servings", sa.Integer(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("preparation_time", sa.Integer(), nullable=True),
        sa.Column("cooking_time", sa.Integer(), nullable=True),
        sa.Column("allergen_notes", sa.Text(), nullable=True),
        sa.Column("image_path", sa.String(length=500), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recipes_id", "recipes", ["id"])
    op.create_index("ix_recipes_name", "recipes", ["name"])

    op.create_table(
        "ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_ingredients_id", "ingredients", ["id"])
    op.create_index("ix_ingredients_name", "ingredients", ["name"])
    op.create_index("ix_ingredients_category", "ingredients", ["category"])

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_tags_id", "tags", ["id"])
    op.create_index("ix_tags_name", "tags", ["name"])

    op.create_table(
        "allergens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_allergens_id", "allergens", ["id"])
    op.create_index("ix_allergens_name", "allergens", ["name"])

    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_app_settings_id", "app_settings", ["id"])

    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"]),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recipe_ingredients_id", "recipe_ingredients", ["id"])
    op.create_index("ix_recipe_ingredients_recipe_id", "recipe_ingredients", ["recipe_id"])
    op.create_index("ix_recipe_ingredients_ingredient_id", "recipe_ingredients", ["ingredient_id"])

    op.create_table(
        "recipe_tags",
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
        sa.PrimaryKeyConstraint("recipe_id", "tag_id"),
    )

    op.create_table(
        "recipe_allergens",
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("allergen_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"]),
        sa.ForeignKeyConstraint(["allergen_id"], ["allergens.id"]),
        sa.PrimaryKeyConstraint("recipe_id", "allergen_id"),
    )

    op.create_table(
        "meal_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("camp_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "camp_id", "meal_date", "meal_type", "position",
            name="uix_meal_plan_position",
        ),
    )
    op.create_index("ix_meal_plans_id", "meal_plans", ["id"])
    op.create_index("ix_meal_plans_camp_id", "meal_plans", ["camp_id"])
    op.create_index("ix_meal_plans_recipe_id", "meal_plans", ["recipe_id"])
    op.create_index("ix_meal_plans_meal_date", "meal_plans", ["meal_date"])
    op.create_index("ix_meal_plans_meal_type", "meal_plans", ["meal_type"])

    op.create_table(
        "recipe_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("base_servings", sa.Integer(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("preparation_time", sa.Integer(), nullable=True),
        sa.Column("cooking_time", sa.Integer(), nullable=True),
        sa.Column("allergen_notes", sa.Text(), nullable=True),
        sa.Column("ingredients_snapshot", sa.Text(), nullable=True),
        sa.Column("tags_snapshot", sa.Text(), nullable=True),
        sa.Column("allergens_snapshot", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recipe_id", "version_number", name="uix_recipe_version"),
    )
    op.create_index("ix_recipe_versions_id", "recipe_versions", ["id"])
    op.create_index("ix_recipe_versions_recipe_id", "recipe_versions", ["recipe_id"])


def downgrade() -> None:
    op.drop_index("ix_recipe_versions_recipe_id", table_name="recipe_versions")
    op.drop_index("ix_recipe_versions_id", table_name="recipe_versions")
    op.drop_table("recipe_versions")

    op.drop_index("ix_meal_plans_meal_type", table_name="meal_plans")
    op.drop_index("ix_meal_plans_meal_date", table_name="meal_plans")
    op.drop_index("ix_meal_plans_recipe_id", table_name="meal_plans")
    op.drop_index("ix_meal_plans_camp_id", table_name="meal_plans")
    op.drop_index("ix_meal_plans_id", table_name="meal_plans")
    op.drop_table("meal_plans")

    op.drop_table("recipe_allergens")
    op.drop_table("recipe_tags")

    op.drop_index("ix_recipe_ingredients_ingredient_id", table_name="recipe_ingredients")
    op.drop_index("ix_recipe_ingredients_recipe_id", table_name="recipe_ingredients")
    op.drop_index("ix_recipe_ingredients_id", table_name="recipe_ingredients")
    op.drop_table("recipe_ingredients")

    op.drop_index("ix_app_settings_id", table_name="app_settings")
    op.drop_table("app_settings")

    op.drop_index("ix_allergens_name", table_name="allergens")
    op.drop_index("ix_allergens_id", table_name="allergens")
    op.drop_table("allergens")

    op.drop_index("ix_tags_name", table_name="tags")
    op.drop_index("ix_tags_id", table_name="tags")
    op.drop_table("tags")

    op.drop_index("ix_ingredients_category", table_name="ingredients")
    op.drop_index("ix_ingredients_name", table_name="ingredients")
    op.drop_index("ix_ingredients_id", table_name="ingredients")
    op.drop_table("ingredients")

    op.drop_index("ix_recipes_name", table_name="recipes")
    op.drop_index("ix_recipes_id", table_name="recipes")
    op.drop_table("recipes")

    op.drop_index("ix_camps_start_date", table_name="camps")
    op.drop_index("ix_camps_id", table_name="camps")
    op.drop_table("camps")
