"""Tests for Story 3: sub_category validator + daily-lists PDF export."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app import crud, models, schemas


def _make_camp(db_session) -> models.Camp:
    return crud.create_camp(
        db_session,
        schemas.CampCreate(
            name="Camp Daily",
            start_date=datetime(2026, 7, 1),
            end_date=datetime(2026, 7, 3),
            participant_count=15,
        ),
    )


def _make_recipe(db_session, name: str = "Gulasch") -> models.Recipe:
    ing = models.Ingredient(name=f"Zutat-{name}", unit="g", category="Sonstiges")
    db_session.add(ing)
    db_session.flush()
    recipe = models.Recipe(
        name=name,
        base_servings=10,
        instructions="1. Anbraten.\n2. Schmoren.\n3. Servieren.",
    )
    db_session.add(recipe)
    db_session.flush()
    db_session.add(
        models.RecipeIngredient(
            recipe_id=recipe.id, ingredient_id=ing.id, quantity=300, unit="g"
        )
    )
    db_session.commit()
    db_session.refresh(recipe)
    return recipe


def _add_meal_plan(db_session, camp_id, recipe_id, meal_type, sub_category=None, date=None, position=0):
    mp = models.MealPlan(
        camp_id=camp_id,
        recipe_id=recipe_id,
        meal_date=date or datetime(2026, 7, 2),
        meal_type=meal_type,
        position=position,
        sub_category=sub_category,
    )
    db_session.add(mp)
    db_session.commit()
    db_session.refresh(mp)
    return mp


def test_sub_category_validator_accepts_known_values(db_session):
    for value in ["Vorspeise", "Hauptgang", "Beilage", "Salat", "Nachtisch"]:
        schemas.MealPlanCreate(
            camp_id=1,
            recipe_id=1,
            meal_date=datetime(2026, 7, 2),
            meal_type=models.MealType.DINNER,
            sub_category=value,
        )


def test_sub_category_validator_accepts_none_and_empty(db_session):
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


def test_daily_pdf_endpoint_returns_pdf(client, db_session):
    camp = _make_camp(db_session)
    recipe = _make_recipe(db_session)
    _add_meal_plan(db_session, camp.id, recipe.id, models.MealType.LUNCH)

    response = client.get(f"/export/daily-lists/pdf/{camp.id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    # PDF magic bytes
    assert response.content[:4] == b"%PDF"


def test_daily_pdf_404_when_no_meal_plans(client, db_session):
    camp = _make_camp(db_session)
    response = client.get(f"/export/daily-lists/pdf/{camp.id}")
    assert response.status_code == 404


def test_daily_pdf_handles_dinner_sub_categories(client, db_session):
    """End-to-end smoke test: dinner with Vorspeise + Hauptgang renders without error."""
    camp = _make_camp(db_session)
    starter = _make_recipe(db_session, "Salat")
    main = _make_recipe(db_session, "Lasagne")

    _add_meal_plan(db_session, camp.id, starter.id, models.MealType.DINNER,
                   sub_category="Vorspeise", position=0)
    _add_meal_plan(db_session, camp.id, main.id, models.MealType.DINNER,
                   sub_category="Hauptgang", position=1)

    response = client.get(f"/export/daily-lists/pdf/{camp.id}")
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
