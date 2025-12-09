from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Table, Boolean, CheckConstraint, UniqueConstraint, Index, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# Enums
class MealType(enum.Enum):
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    DINNER = "DINNER"

# Association tables for many-to-many relationships
recipe_tag_table = Table(
    'recipe_tags',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

recipe_allergen_table = Table(
    'recipe_allergens',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id'), primary_key=True),
    Column('allergen_id', Integer, ForeignKey('allergens.id'), primary_key=True)
)

class Camp(Base):
    __tablename__ = 'camps'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False)
    participant_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)

    # Relationships
    meal_plans = relationship("MealPlan", back_populates="camp", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint('start_date <= end_date', name='check_camp_date_range'),
        CheckConstraint('participant_count > 0', name='check_camp_participant_count_positive'),
    )

class Recipe(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    base_servings = Column(Integer, nullable=False, default=30)
    instructions = Column(Text)
    preparation_time = Column(Integer)  # in minutes
    cooking_time = Column(Integer)  # in minutes
    allergen_notes = Column(Text)
    image_path = Column(String(500))  # path to recipe image
    version_number = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=recipe_tag_table, back_populates="recipes")
    allergens = relationship("Allergen", secondary=recipe_allergen_table, back_populates="recipes")
    meal_plans = relationship("MealPlan", back_populates="recipe")
    versions = relationship("RecipeVersion", back_populates="recipe", cascade="all, delete-orphan")

class Ingredient(Base):
    __tablename__ = 'ingredients'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    unit = Column(String(50), nullable=False)  # g, kg, L, ml, Stück, custom
    category = Column(String(100), nullable=False, index=True)  # Obst, Gemüse, Milchprodukte, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient")

class RecipeIngredient(Base):
    __tablename__ = 'recipe_ingredients'

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False, index=True)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    color = Column(String(7), default="#3B82F6")  # Hex color
    icon = Column(String(50))  # Icon name or emoji
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recipes = relationship("Recipe", secondary=recipe_tag_table, back_populates="tags")

class MealPlan(Base):
    __tablename__ = 'meal_plans'

    id = Column(Integer, primary_key=True, index=True)
    camp_id = Column(Integer, ForeignKey('camps.id'), nullable=False, index=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False, index=True)
    meal_date = Column(DateTime, nullable=False, index=True)
    meal_type = Column(Enum(MealType), nullable=False, index=True)
    position = Column(Integer, default=0)  # for multiple recipes per slot
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    camp = relationship("Camp", back_populates="meal_plans")
    recipe = relationship("Recipe", back_populates="meal_plans")

    # Constraints
    __table_args__ = (
        UniqueConstraint('camp_id', 'meal_date', 'meal_type', 'position',
                         name='uix_meal_plan_position'),
    )

class Allergen(Base):
    __tablename__ = 'allergens'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    icon = Column(String(50))  # Icon/emoji for allergen (🥜, 🥛, 🌾, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recipes = relationship("Recipe", secondary=recipe_allergen_table, back_populates="allergens")

class RecipeVersion(Base):
    __tablename__ = 'recipe_versions'

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    base_servings = Column(Integer, nullable=False)
    instructions = Column(Text)
    preparation_time = Column(Integer)
    cooking_time = Column(Integer)
    allergen_notes = Column(Text)
    ingredients_snapshot = Column(Text)  # JSON snapshot of ingredients at this version
    tags_snapshot = Column(Text)  # JSON snapshot of tags at this version
    allergens_snapshot = Column(Text)  # JSON snapshot of allergens at this version
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recipe = relationship("Recipe", back_populates="versions")

    # Constraints
    __table_args__ = (
        UniqueConstraint('recipe_id', 'version_number',
                         name='uix_recipe_version'),
    )

class AppSettings(Base):
    __tablename__ = 'app_settings'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text, nullable=False)  # JSON string

    def __repr__(self):
        return f"<AppSettings(key='{self.key}', value='{self.value}')>"