"""Pydantic-Schema validation tests.

Validates the constraints documented in `app.schemas`:
  * `CampBase.participant_count > 0`
  * `CampBase`: `end_date >= start_date`
  * `RecipeIngredientCreate.quantity > 0`
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app import schemas


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
