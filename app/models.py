from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Table, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Association tables for many-to-many relationships
recipe_tag_table = Table(
    'recipe_tags',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Camp(Base):
    __tablename__ = 'camps'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    participant_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    meal_plans = relationship("MealPlan", back_populates="camp", cascade="all, delete-orphan")

class Recipe(Base):
    __tablename__ = 'recipes'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    base_servings = Column(Integer, nullable=False, default=30)
    instructions = Column(Text)
    preparation_time = Column(Integer)  # in minutes
    cooking_time = Column(Integer)  # in minutes
    allergens = Column(Text)  # comma-separated
    allergen_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=recipe_tag_table, back_populates="recipes")
    meal_plans = relationship("MealPlan", back_populates="recipe")

class Ingredient(Base):
    __tablename__ = 'ingredients'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    unit = Column(String(50), nullable=False)  # g, kg, L, ml, Stück, custom
    category = Column(String(100), nullable=False)  # Obst, Gemüse, Milchprodukte, etc.
    
    # Relationships
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient")

class RecipeIngredient(Base):
    __tablename__ = 'recipe_ingredients'
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), default="#3B82F6")  # Hex color
    icon = Column(String(50))  # Icon name or emoji
    
    # Relationships
    recipes = relationship("Recipe", secondary=recipe_tag_table, back_populates="tags")

class MealPlan(Base):
    __tablename__ = 'meal_plans'
    
    id = Column(Integer, primary_key=True, index=True)
    camp_id = Column(Integer, ForeignKey('camps.id'), nullable=False)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)
    meal_date = Column(DateTime, nullable=False)
    meal_type = Column(String(20), nullable=False)  # BREAKFAST, LUNCH, DINNER
    position = Column(Integer, default=0)  # for multiple recipes per slot
    notes = Column(Text)
    
    # Relationships
    camp = relationship("Camp", back_populates="meal_plans")
    recipe = relationship("Recipe", back_populates="meal_plans")

class AppSettings(Base):
    __tablename__ = 'app_settings'
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text, nullable=False)  # JSON string
    
    def __repr__(self):
        return f"<AppSettings(key='{self.key}', value='{self.value}')>"