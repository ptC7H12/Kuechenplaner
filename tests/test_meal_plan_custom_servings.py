"""Tests for Story 1: custom_servings override on MealPlan."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app import crud, models, schemas
from app.services.calculation import calculate_shopping_list


def _make_camp(db_session, participant_count: int = 10) -> models.Camp:
    return crud.create_camp(
        db_session,
        schemas.CampCreate(
            name="Camp Custom",
            start_date=datetime(2026, 7, 1),
            end_date=datetime(2026, 7, 7),
            participant_count=participant_count,
        ),
    )


def _make_recipe_with_ingredient(db_session) -> tuple[models.Recipe, models.Ingredient]:
    ing = models.Ingredient(name="Reis", unit="g", category="Getreide")
    db_session.add(ing)
    db_session.flush()

    recipe = models.Recipe(name="Reisgericht", base_servings=10)
    db_session.add(recipe)
    db_session.flush()
    db_session.add(
        models.RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ing.id,
            quantity=100,
            unit="g",
        )
    )
    db_session.commit()
    db_session.refresh(recipe)
    return recipe, ing


def _add_meal_plan(db_session, camp_id, recipe_id, custom_servings=None, position=0):
    mp = models.MealPlan(
        camp_id=camp_id,
        recipe_id=recipe_id,
        meal_date=datetime(2026, 7, 2),
        meal_type=models.MealType.LUNCH,
        position=position,
        custom_servings=custom_servings,
    )
    db_session.add(mp)
    db_session.commit()
    db_session.refresh(mp)
    return mp


def test_custom_servings_overrides_camp_for_scaling(db_session):
    camp = _make_camp(db_session, participant_count=10)
    recipe, _ = _make_recipe_with_ingredient(db_session)
    _add_meal_plan(db_session, camp.id, recipe.id, custom_servings=20)

    result = calculate_shopping_list(db_session, camp.id)
    items = result["items"]
    assert len(items) == 1
    # base 10 servings → 100 g; custom 20 → 200 g
    assert items[0]["original_quantity"] == pytest.approx(200.0)


def test_falls_back_to_camp_participants_when_no_override(db_session):
    camp = _make_camp(db_session, participant_count=10)
    recipe, _ = _make_recipe_with_ingredient(db_session)
    _add_meal_plan(db_session, camp.id, recipe.id, custom_servings=None)

    result = calculate_shopping_list(db_session, camp.id)
    # 100 g base for 10 servings, camp has 10 → 100 g
    assert result["items"][0]["original_quantity"] == pytest.approx(100.0)


def test_shopping_list_aggregates_mixed_servings(db_session):
    """Two meal plans of the same recipe with different servings: quantities add up."""
    camp = _make_camp(db_session, participant_count=10)
    recipe, _ = _make_recipe_with_ingredient(db_session)
    _add_meal_plan(db_session, camp.id, recipe.id, custom_servings=5, position=0)
    _add_meal_plan(db_session, camp.id, recipe.id, custom_servings=20, position=1)

    result = calculate_shopping_list(db_session, camp.id)
    # 50 g + 200 g = 250 g
    assert result["items"][0]["original_quantity"] == pytest.approx(250.0)


def test_custom_servings_must_be_positive(db_session):
    """Pydantic rejects custom_servings <= 0."""
    with pytest.raises(ValidationError):
        schemas.MealPlanCreate(
            camp_id=1,
            recipe_id=1,
            meal_date=datetime(2026, 7, 2),
            meal_type=models.MealType.LUNCH,
            custom_servings=0,
        )

    with pytest.raises(ValidationError):
        schemas.MealPlanUpdate(custom_servings=-5)


def test_meal_plan_update_can_clear_custom_servings(db_session):
    """Sending custom_servings=null via update resets the override."""
    camp = _make_camp(db_session)
    recipe, _ = _make_recipe_with_ingredient(db_session)
    mp = _add_meal_plan(db_session, camp.id, recipe.id, custom_servings=42)
    assert mp.custom_servings == 42

    updated = crud.update_meal_plan(
        db_session, mp.id, schemas.MealPlanUpdate(custom_servings=None)
    )
    assert updated.custom_servings is None


def test_custom_servings_endpoint_round_trip(client, db_session):
    """The PUT endpoint accepts the custom_servings field."""
    camp = _make_camp(db_session)
    recipe, _ = _make_recipe_with_ingredient(db_session)
    mp = _add_meal_plan(db_session, camp.id, recipe.id)

    response = client.put(
        f"/meal-planning/api/meal-plans/{mp.id}",
        json={"custom_servings": 25},
    )
    assert response.status_code == 200
    assert response.json()["custom_servings"] == 25

    response = client.put(
        f"/meal-planning/api/meal-plans/{mp.id}",
        json={"custom_servings": 0},
    )
    assert response.status_code == 422  # rejected by Pydantic gt=0
