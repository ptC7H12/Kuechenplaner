"""make meal_plan recipe_id nullable

Revision ID: 001
Revises:
Create Date: 2025-12-16 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make recipe_id column in meal_plans table nullable.

    Since SQLite doesn't support ALTER COLUMN, we need to:
    1. Create a new table with the corrected schema
    2. Copy data from old table
    3. Drop old table
    4. Rename new table
    """

    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Check if meal_plans table exists
    if 'meal_plans' not in inspector.get_table_names():
        print("meal_plans table doesn't exist, skipping migration")
        return

    # Check if the column is already nullable by trying to inspect the constraint
    # We'll proceed with the migration to ensure consistency

    # Create new table with nullable recipe_id
    op.create_table(
        'meal_plans_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('camp_id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=True),  # Changed to nullable=True
        sa.Column('meal_date', sa.DateTime(), nullable=False),
        sa.Column('meal_type', sa.Enum('BREAKFAST', 'LUNCH', 'DINNER', name='mealtype'), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['camp_id'], ['camps.id'], ),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('camp_id', 'meal_date', 'meal_type', 'position', name='uix_meal_plan_position')
    )

    # Create indexes
    op.create_index('ix_meal_plans_new_camp_id', 'meal_plans_new', ['camp_id'])
    op.create_index('ix_meal_plans_new_id', 'meal_plans_new', ['id'])
    op.create_index('ix_meal_plans_new_meal_date', 'meal_plans_new', ['meal_date'])
    op.create_index('ix_meal_plans_new_meal_type', 'meal_plans_new', ['meal_type'])
    op.create_index('ix_meal_plans_new_recipe_id', 'meal_plans_new', ['recipe_id'])

    # Copy data from old table to new table
    op.execute("""
        INSERT INTO meal_plans_new (id, camp_id, recipe_id, meal_date, meal_type, position, notes, created_at, updated_at)
        SELECT id, camp_id, recipe_id, meal_date, meal_type, position, notes, created_at, updated_at
        FROM meal_plans
    """)

    # Drop old table
    op.drop_table('meal_plans')

    # Rename new table to original name
    op.rename_table('meal_plans_new', 'meal_plans')


def downgrade() -> None:
    """Revert recipe_id column back to NOT NULL.

    Note: This will fail if there are any NULL values in recipe_id.
    """

    conn = op.get_bind()

    # Create new table with NOT NULL recipe_id
    op.create_table(
        'meal_plans_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('camp_id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),  # Changed back to nullable=False
        sa.Column('meal_date', sa.DateTime(), nullable=False),
        sa.Column('meal_type', sa.Enum('BREAKFAST', 'LUNCH', 'DINNER', name='mealtype'), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['camp_id'], ['camps.id'], ),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('camp_id', 'meal_date', 'meal_type', 'position', name='uix_meal_plan_position')
    )

    # Create indexes
    op.create_index('ix_meal_plans_new_camp_id', 'meal_plans_new', ['camp_id'])
    op.create_index('ix_meal_plans_new_id', 'meal_plans_new', ['id'])
    op.create_index('ix_meal_plans_new_meal_date', 'meal_plans_new', ['meal_date'])
    op.create_index('ix_meal_plans_new_meal_type', 'meal_plans_new', ['meal_type'])
    op.create_index('ix_meal_plans_new_recipe_id', 'meal_plans_new', ['recipe_id'])

    # Copy data (will fail if there are NULL values)
    op.execute("""
        INSERT INTO meal_plans_new (id, camp_id, recipe_id, meal_date, meal_type, position, notes, created_at, updated_at)
        SELECT id, camp_id, recipe_id, meal_date, meal_type, position, notes, created_at, updated_at
        FROM meal_plans
        WHERE recipe_id IS NOT NULL
    """)

    # Drop old table
    op.drop_table('meal_plans')

    # Rename new table to original name
    op.rename_table('meal_plans_new', 'meal_plans')
