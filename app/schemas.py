from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from app.models import MealType

# Base schemas
class CampBase(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime
    participant_count: int

class CampCreate(CampBase):
    pass

class CampUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    participant_count: Optional[int] = None

class Camp(CampBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_accessed: datetime
    
    class Config:
        from_attributes = True

# Recipe schemas
class IngredientBase(BaseModel):
    name: str
    unit: str
    category: str

class IngredientCreate(IngredientBase):
    pass

class Ingredient(IngredientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RecipeIngredientBase(BaseModel):
    ingredient_id: int
    quantity: float
    unit: str

class RecipeIngredientCreate(RecipeIngredientBase):
    pass

class RecipeIngredient(RecipeIngredientBase):
    id: int
    ingredient: Ingredient
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TagBase(BaseModel):
    name: str
    color: str = "#3B82F6"
    icon: Optional[str] = None

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Allergen schemas
class AllergenBase(BaseModel):
    name: str
    icon: Optional[str] = None

class AllergenCreate(AllergenBase):
    pass

class Allergen(AllergenBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RecipeBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_servings: int = 30
    instructions: Optional[str] = None
    preparation_time: Optional[int] = None
    cooking_time: Optional[int] = None
    allergen_notes: Optional[str] = None
    image_path: Optional[str] = None

class RecipeCreate(RecipeBase):
    ingredients: List[RecipeIngredientCreate] = []
    tag_ids: List[int] = []
    allergen_ids: List[int] = []

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_servings: Optional[int] = None
    instructions: Optional[str] = None
    preparation_time: Optional[int] = None
    cooking_time: Optional[int] = None
    allergen_notes: Optional[str] = None
    image_path: Optional[str] = None
    ingredients: Optional[List[RecipeIngredientCreate]] = None
    tag_ids: Optional[List[int]] = None
    allergen_ids: Optional[List[int]] = None

class Recipe(RecipeBase):
    id: int
    version_number: int
    created_at: datetime
    updated_at: datetime
    ingredients: List[RecipeIngredient] = []
    tags: List[Tag] = []
    allergens: List[Allergen] = []

    class Config:
        from_attributes = True

# Meal Plan schemas
class MealPlanBase(BaseModel):
    recipe_id: Optional[int] = None  # Optional for "no meal" entries
    meal_date: datetime
    meal_type: MealType
    position: int = 0
    notes: Optional[str] = None

class MealPlanCreate(MealPlanBase):
    camp_id: int

class MealPlanUpdate(BaseModel):
    position: Optional[int] = None
    notes: Optional[str] = None

class MealPlan(MealPlanBase):
    id: int
    camp_id: int
    recipe: Optional[Recipe] = None  # Optional for "no meal" entries
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Settings schemas
class AppSettingsBase(BaseModel):
    key: str
    value: str

class AppSettingsCreate(AppSettingsBase):
    pass

class AppSettings(AppSettingsBase):
    id: int
    
    class Config:
        from_attributes = True

# Shopping list schemas
class ShoppingListItem(BaseModel):
    ingredient: Ingredient
    quantity: float
    unit: str
    category: str

class ShoppingList(BaseModel):
    items: List[ShoppingListItem]
    categories: List[str]

# Recipe Version schemas
class RecipeVersionBase(BaseModel):
    recipe_id: int
    version_number: int
    name: str
    description: Optional[str] = None
    base_servings: int
    instructions: Optional[str] = None
    preparation_time: Optional[int] = None
    cooking_time: Optional[int] = None
    allergen_notes: Optional[str] = None
    ingredients_snapshot: str  # JSON
    tags_snapshot: str  # JSON
    allergens_snapshot: str  # JSON

class RecipeVersionCreate(RecipeVersionBase):
    pass

class RecipeVersion(RecipeVersionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True