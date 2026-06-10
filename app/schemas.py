from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.constants import MEAL_SUB_CATEGORIES
from app.models import MealType


# Base schemas
class CampBase(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime
    participant_count: int = Field(gt=0)

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date muss nach start_date liegen")
        return self


class CampCreate(CampBase):
    pass


class CampUpdate(BaseModel):
    name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    participant_count: int | None = Field(None, gt=0)


class Camp(CampBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    last_accessed: datetime


# Category schemas
class CategoryBase(BaseModel):
    name: str
    color: str = "#6B7280"

    @field_validator("name")
    @classmethod
    def _name_not_empty(cls, v):
        if v is None or not v.strip():
            raise ValueError("name darf nicht leer sein")
        return v.strip()


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# Recipe schemas
class IngredientBase(BaseModel):
    name: str
    unit: str
    category_id: int | None = None
    note: str | None = None


class IngredientCreate(IngredientBase):
    pass


class IngredientUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    category_id: int | None = None
    note: str | None = None


class Ingredient(IngredientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: Category | None = None
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
    icon: str | None = None


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
    icon: str | None = None


class AllergenCreate(AllergenBase):
    pass


class Allergen(AllergenBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class RecipeBase(BaseModel):
    name: str
    description: str | None = None
    base_servings: int = Field(30, gt=0)
    instructions: str | None = None
    preparation_time: int | None = Field(None, ge=0)
    cooking_time: int | None = Field(None, ge=0)
    allergen_notes: str | None = None
    image_path: str | None = None


class RecipeCreate(RecipeBase):
    ingredients: list[RecipeIngredientCreate] = []
    tag_ids: list[int] = []
    allergen_ids: list[int] = []


class RecipeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    base_servings: int | None = Field(None, gt=0)
    instructions: str | None = None
    preparation_time: int | None = Field(None, ge=0)
    cooking_time: int | None = Field(None, ge=0)
    allergen_notes: str | None = None
    image_path: str | None = None
    ingredients: list[RecipeIngredientCreate] | None = None
    tag_ids: list[int] | None = None
    allergen_ids: list[int] | None = None


class Recipe(RecipeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_number: int
    created_at: datetime
    updated_at: datetime
    ingredients: list[RecipeIngredient] = []
    tags: list[Tag] = []
    allergens: list[Allergen] = []


# Meal Plan schemas
def _validate_sub_category(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if value not in MEAL_SUB_CATEGORIES:
        raise ValueError(f"sub_category muss einer von {MEAL_SUB_CATEGORIES} sein oder leer")
    return value


class MealPlanBase(BaseModel):
    recipe_id: int | None = None  # Optional for "no meal" entries
    meal_date: datetime
    meal_type: MealType
    position: int = 0
    notes: str | None = None
    custom_servings: int | None = Field(None, gt=0)
    sub_category: str | None = None

    @field_validator("sub_category")
    @classmethod
    def _check_sub_category(cls, v):
        return _validate_sub_category(v)


class MealPlanCreate(MealPlanBase):
    camp_id: int


class MealPlanUpdate(BaseModel):
    position: int | None = None
    notes: str | None = None
    custom_servings: int | None = Field(None, gt=0)
    sub_category: str | None = None

    @field_validator("sub_category")
    @classmethod
    def _check_sub_category(cls, v):
        return _validate_sub_category(v)


class MealPlan(MealPlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camp_id: int
    recipe: Recipe | None = None  # Optional for "no meal" entries
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
    note: str | None = None  # Camp-specific note for this shopping list
    global_note: str | None = None  # Global note from Ingredient.note


class ShoppingList(BaseModel):
    items: list[ShoppingListItem]
    categories: list[str]


class ShoppingListNoteUpdate(BaseModel):
    note: str  # Empty string deletes the camp-specific note


# Leftover schemas
class LeftoverBase(BaseModel):
    camp_id: int
    meal_plan_id: int | None = None
    recipe_id: int | None = None
    ingredient_id: int | None = None
    tracking_type: str  # "per_recipe" or "per_ingredient"
    percentage_left: float | None = Field(None, ge=0, le=100)
    description: str | None = None

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
    tracking_type: str | None = None
    ingredient_id: int | None = None
    percentage_left: float | None = Field(None, ge=0, le=100)
    description: str | None = None

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
    ingredient_id: int | None = None
    percentage_left: float | None = Field(None, ge=0, le=100)
    description: str | None = None

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
    entries: list[LeftoverEntryIn]


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
    avg_percentage_left: float | None = None
    suggested_servings: int | None = None
    base_camp_participants: int | None = None


# Recipe Version schemas
class RecipeVersionBase(BaseModel):
    recipe_id: int
    version_number: int
    name: str
    description: str | None = None
    base_servings: int
    instructions: str | None = None
    preparation_time: int | None = None
    cooking_time: int | None = None
    allergen_notes: str | None = None
    ingredients_snapshot: str  # JSON
    tags_snapshot: str  # JSON
    allergens_snapshot: str  # JSON


class RecipeVersionCreate(RecipeVersionBase):
    pass


class RecipeVersion(RecipeVersionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
