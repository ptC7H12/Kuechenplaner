from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict
from datetime import datetime
from typing import List, Optional
from app.models import MealType
from app.constants import MEAL_SUB_CATEGORIES

# Base schemas
class CampBase(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime
    participant_count: int = Field(gt=0)

    @model_validator(mode='after')
    def check_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError('end_date muss nach start_date liegen')
        return self

class CampCreate(CampBase):
    pass

class CampUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    participant_count: Optional[int] = Field(None, gt=0)

class Camp(CampBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    last_accessed: datetime

# Recipe schemas
class IngredientBase(BaseModel):
    name: str
    unit: str
    category: str
    note: Optional[str] = None

class IngredientCreate(IngredientBase):
    pass

class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    note: Optional[str] = None

class Ingredient(IngredientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

class RecipeIngredientBase(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0)
    unit: str

class RecipeIngredientCreate(RecipeIngredientBase):
    pass

class RecipeIngredient(RecipeIngredientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient: Ingredient
    created_at: datetime
    updated_at: datetime

class TagBase(BaseModel):
    name: str
    color: str = "#3B82F6"
    icon: Optional[str] = None

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

# Allergen schemas
class AllergenBase(BaseModel):
    name: str
    icon: Optional[str] = None

class AllergenCreate(AllergenBase):
    pass

class Allergen(AllergenBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

class RecipeBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_servings: int = Field(30, gt=0)
    instructions: Optional[str] = None
    preparation_time: Optional[int] = Field(None, ge=0)
    cooking_time: Optional[int] = Field(None, ge=0)
    allergen_notes: Optional[str] = None
    image_path: Optional[str] = None

class RecipeCreate(RecipeBase):
    ingredients: List[RecipeIngredientCreate] = []
    tag_ids: List[int] = []
    allergen_ids: List[int] = []

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_servings: Optional[int] = Field(None, gt=0)
    instructions: Optional[str] = None
    preparation_time: Optional[int] = Field(None, ge=0)
    cooking_time: Optional[int] = Field(None, ge=0)
    allergen_notes: Optional[str] = None
    image_path: Optional[str] = None
    ingredients: Optional[List[RecipeIngredientCreate]] = None
    tag_ids: Optional[List[int]] = None
    allergen_ids: Optional[List[int]] = None

class Recipe(RecipeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_number: int
    created_at: datetime
    updated_at: datetime
    ingredients: List[RecipeIngredient] = []
    tags: List[Tag] = []
    allergens: List[Allergen] = []

# Meal Plan schemas
def _validate_sub_category(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    if value not in MEAL_SUB_CATEGORIES:
        raise ValueError(
            f"sub_category muss einer von {MEAL_SUB_CATEGORIES} sein oder leer"
        )
    return value


class MealPlanBase(BaseModel):
    recipe_id: Optional[int] = None  # Optional for "no meal" entries
    meal_date: datetime
    meal_type: MealType
    position: int = 0
    notes: Optional[str] = None
    custom_servings: Optional[int] = Field(None, gt=0)
    sub_category: Optional[str] = None

    @field_validator("sub_category")
    @classmethod
    def _check_sub_category(cls, v):
        return _validate_sub_category(v)

class MealPlanCreate(MealPlanBase):
    camp_id: int

class MealPlanUpdate(BaseModel):
    position: Optional[int] = None
    notes: Optional[str] = None
    custom_servings: Optional[int] = Field(None, gt=0)
    sub_category: Optional[str] = None

    @field_validator("sub_category")
    @classmethod
    def _check_sub_category(cls, v):
        return _validate_sub_category(v)

class MealPlan(MealPlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camp_id: int
    recipe: Optional[Recipe] = None  # Optional for "no meal" entries
    created_at: datetime
    updated_at: datetime

# Settings schemas
class AppSettingsBase(BaseModel):
    key: str
    value: str

class AppSettingsCreate(AppSettingsBase):
    pass

class AppSettings(AppSettingsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

# Shopping list schemas
class ShoppingListItem(BaseModel):
    ingredient: Ingredient
    quantity: float
    unit: str
    category: str
    note: Optional[str] = None         # Camp-specific note for this shopping list
    global_note: Optional[str] = None  # Global note from Ingredient.note

class ShoppingList(BaseModel):
    items: List[ShoppingListItem]
    categories: List[str]

class ShoppingListNoteUpdate(BaseModel):
    note: str  # Empty string deletes the camp-specific note

# Leftover schemas
class LeftoverBase(BaseModel):
    camp_id: int
    meal_plan_id: Optional[int] = None
    recipe_id: Optional[int] = None
    ingredient_id: Optional[int] = None
    tracking_type: str  # "per_recipe" or "per_ingredient"
    percentage_left: Optional[float] = Field(None, ge=0, le=100)
    description: Optional[str] = None

    @field_validator("tracking_type")
    @classmethod
    def _check_tracking_type(cls, v):
        if v not in {"per_recipe", "per_ingredient"}:
            raise ValueError("tracking_type muss 'per_recipe' oder 'per_ingredient' sein")
        return v

    @model_validator(mode="after")
    def _check_ingredient_for_per_ingredient(self):
        if self.tracking_type == "per_ingredient" and self.ingredient_id is None:
            raise ValueError("ingredient_id ist bei tracking_type 'per_ingredient' erforderlich")
        return self


class LeftoverCreate(LeftoverBase):
    pass


class LeftoverUpdate(BaseModel):
    tracking_type: Optional[str] = None
    ingredient_id: Optional[int] = None
    percentage_left: Optional[float] = Field(None, ge=0, le=100)
    description: Optional[str] = None

    @field_validator("tracking_type")
    @classmethod
    def _check_tracking_type(cls, v):
        if v is None:
            return v
        if v not in {"per_recipe", "per_ingredient"}:
            raise ValueError("tracking_type muss 'per_recipe' oder 'per_ingredient' sein")
        return v


class LeftoverEntryIn(BaseModel):
    """One measurement in a meal-plan sync payload (Story 7).

    camp_id, meal_plan_id and recipe_id come from the URL/MealPlan,
    not from the entry itself.
    """
    tracking_type: str
    ingredient_id: Optional[int] = None
    percentage_left: Optional[float] = Field(None, ge=0, le=100)
    description: Optional[str] = None

    @field_validator("tracking_type")
    @classmethod
    def _check_tracking_type(cls, v):
        if v not in {"per_recipe", "per_ingredient"}:
            raise ValueError("tracking_type muss 'per_recipe' oder 'per_ingredient' sein")
        return v

    @model_validator(mode="after")
    def _check_ingredient_for_per_ingredient(self):
        if self.tracking_type == "per_ingredient" and self.ingredient_id is None:
            raise ValueError("ingredient_id ist bei tracking_type 'per_ingredient' erforderlich")
        return self


class LeftoverSyncRequest(BaseModel):
    entries: List[LeftoverEntryIn]


class Leftover(LeftoverBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class LeftoverStatistics(BaseModel):
    recipe_id: int
    recipe_name: str
    total_entries: int
    camps_with_leftovers: int
    avg_percentage_left: Optional[float] = None
    suggested_servings: Optional[int] = None
    base_camp_participants: Optional[int] = None


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
