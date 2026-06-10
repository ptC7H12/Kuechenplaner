"""Pydantic-Schema validation tests.

Validates the constraints documented in `app.schemas`:
  * `CampBase.participant_count > 0`
  * `CampBase`: `end_date >= start_date`
  * `RecipeIngredientCreate.quantity > 0`
  * `MealPlanCreate.sub_category` whitelist
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app import models, schemas


def test_camp_rejects_zero_participants():
    with pytest.raises(ValidationError):
        schemas.CampCreate(
            name="X",
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 1, 5),
            participant_count=0,
        )


def test_camp_rejects_end_before_start():
    with pytest.raises(ValidationError):
        schemas.CampCreate(
            name="X",
            start_date=datetime(2026, 1, 5),
            end_date=datetime(2026, 1, 1),
            participant_count=10,
        )


def test_camp_accepts_same_day_start_and_end():
    same_day = datetime(2026, 1, 1)
    camp = schemas.CampCreate(
        name="X",
        start_date=same_day,
        end_date=same_day,
        participant_count=5,
    )
    assert camp.start_date == camp.end_date


def test_recipe_ingredient_rejects_non_positive_quantity():
    with pytest.raises(ValidationError):
        schemas.RecipeIngredientCreate(ingredient_id=1, quantity=0, unit="g")


def test_recipe_rejects_negative_preparation_time():
    with pytest.raises(ValidationError):
        schemas.RecipeCreate(name="Test", base_servings=10, preparation_time=-5)


def test_sub_category_validator_accepts_known_values():
    for value in ["Vorspeise", "Hauptgang", "Beilage", "Salat", "Nachtisch"]:
        schemas.MealPlanCreate(
            camp_id=1,
            recipe_id=1,
            meal_date=datetime(2026, 7, 2),
            meal_type=models.MealType.DINNER,
            sub_category=value,
        )


def test_sub_category_validator_accepts_none_and_empty():
    mp = schemas.MealPlanCreate(
        camp_id=1,
        recipe_id=1,
        meal_date=datetime(2026, 7, 2),
        meal_type=models.MealType.DINNER,
        sub_category=None,
    )
    assert mp.sub_category is None
    # Empty string is normalised to None.
    mp2 = schemas.MealPlanCreate(
        camp_id=1,
        recipe_id=1,
        meal_date=datetime(2026, 7, 2),
        meal_type=models.MealType.DINNER,
        sub_category="",
    )
    assert mp2.sub_category is None


def test_sub_category_validator_rejects_invalid_values():
    with pytest.raises(ValidationError):
        schemas.MealPlanCreate(
            camp_id=1,
            recipe_id=1,
            meal_date=datetime(2026, 7, 2),
            meal_type=models.MealType.DINNER,
            sub_category="Brunch",
        )
    with pytest.raises(ValidationError):
        schemas.MealPlanUpdate(sub_category="Nachspeise")
