"""Tests for Story 5: leftover tracking + per-recipe statistics."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app import crud, models, schemas
from app.services.leftover_statistics import get_recipe_statistics


def _make_camp(db_session, name: str = "Camp", participant_count: int = 50) -> models.Camp:
    return crud.create_camp(
        db_session,
        schemas.CampCreate(
            name=name,
            start_date=datetime(2026, 7, 1),
            end_date=datetime(2026, 7, 7),
            participant_count=participant_count,
        ),
    )


def _make_recipe(db_session, name: str = "Pizzasuppe") -> models.Recipe:
    recipe = models.Recipe(name=name, base_servings=20)
    db_session.add(recipe)
    db_session.commit()
    db_session.refresh(recipe)
    return recipe


def _make_ingredient(db_session, name: str = "Nudeln") -> models.Ingredient:
    ing = models.Ingredient(name=name, unit="g")
    db_session.add(ing)
    db_session.commit()
    db_session.refresh(ing)
    return ing


def test_create_leftover_per_recipe(db_session):
    camp = _make_camp(db_session)
    recipe = _make_recipe(db_session)
    leftover = crud.create_leftover(
        db_session,
        schemas.LeftoverCreate(
            camp_id=camp.id,
            recipe_id=recipe.id,
            tracking_type="per_recipe",
            percentage_left=15.0,
            description="ein Topf uebrig",
        ),
    )
    assert leftover.id is not None
    assert leftover.tracking_type == "per_recipe"
    assert leftover.percentage_left == 15.0


def test_per_ingredient_requires_ingredient_id():
    with pytest.raises(ValidationError):
        schemas.LeftoverCreate(
            camp_id=1,
            tracking_type="per_ingredient",
            percentage_left=10.0,
        )


def test_per_ingredient_with_ingredient_id_works(db_session):
    camp = _make_camp(db_session)
    ing = _make_ingredient(db_session)
    leftover = crud.create_leftover(
        db_session,
        schemas.LeftoverCreate(
            camp_id=camp.id,
            ingredient_id=ing.id,
            tracking_type="per_ingredient",
            percentage_left=30.0,
        ),
    )
    assert leftover.ingredient_id == ing.id


def test_percentage_must_be_0_to_100():
    with pytest.raises(ValidationError):
        schemas.LeftoverCreate(
            camp_id=1,
            recipe_id=1,
            tracking_type="per_recipe",
            percentage_left=150.0,
        )
    with pytest.raises(ValidationError):
        schemas.LeftoverCreate(
            camp_id=1,
            recipe_id=1,
            tracking_type="per_recipe",
            percentage_left=-5.0,
        )


def test_tracking_type_rejects_unknown_values():
    with pytest.raises(ValidationError):
        schemas.LeftoverCreate(
            camp_id=1,
            recipe_id=1,
            tracking_type="bogus",
        )


def test_statistics_aggregates_over_multiple_camps(db_session):
    recipe = _make_recipe(db_session)
    camp_a = _make_camp(db_session, "A", participant_count=40)
    camp_b = _make_camp(db_session, "B", participant_count=50)

    crud.create_leftover(
        db_session,
        schemas.LeftoverCreate(
            camp_id=camp_a.id,
            recipe_id=recipe.id,
            tracking_type="per_recipe",
            percentage_left=20.0,
        ),
    )
    crud.create_leftover(
        db_session,
        schemas.LeftoverCreate(
            camp_id=camp_b.id,
            recipe_id=recipe.id,
            tracking_type="per_recipe",
            percentage_left=30.0,
        ),
    )

    stats = get_recipe_statistics(db_session, recipe.id)
    assert stats["total_entries"] == 2
    assert stats["camps_with_leftovers"] == 2
    assert stats["avg_percentage_left"] == pytest.approx(25.0)


def test_statistics_suggests_smaller_servings_when_leftovers_high(db_session):
    recipe = _make_recipe(db_session)
    camp = _make_camp(db_session, participant_count=45)
    crud.create_leftover(
        db_session,
        schemas.LeftoverCreate(
            camp_id=camp.id,
            recipe_id=recipe.id,
            tracking_type="per_recipe",
            percentage_left=20.0,
        ),
    )

    stats = get_recipe_statistics(db_session, recipe.id, current_camp_id=camp.id)
    # 45 * (1 - 0.20) = 36
    assert stats["suggested_servings"] == 36
    assert stats["base_camp_participants"] == 45


def test_statistics_no_suggestion_when_leftovers_low(db_session):
    recipe = _make_recipe(db_session)
    camp = _make_camp(db_session)
    crud.create_leftover(
        db_session,
        schemas.LeftoverCreate(
            camp_id=camp.id,
            recipe_id=recipe.id,
            tracking_type="per_recipe",
            percentage_left=5.0,
        ),
    )

    stats = get_recipe_statistics(db_session, recipe.id, current_camp_id=camp.id)
    assert stats["suggested_servings"] is None


def test_leftover_cascades_on_camp_delete(db_session):
    camp = _make_camp(db_session)
    recipe = _make_recipe(db_session)
    crud.create_leftover(
        db_session,
        schemas.LeftoverCreate(
            camp_id=camp.id,
            recipe_id=recipe.id,
            tracking_type="per_recipe",
            percentage_left=10.0,
        ),
    )
    assert len(crud.get_leftovers_for_camp(db_session, camp.id)) == 1

    crud.delete_camp(db_session, camp.id)
    # CASCADE: leftovers gone with the camp.
    assert db_session.query(models.Leftover).count() == 0


def test_leftover_create_endpoint_round_trip(client, db_session):
    camp = _make_camp(db_session)
    recipe = _make_recipe(db_session)
    response = client.post(
        "/leftovers/api/leftovers",
        json={
            "camp_id": camp.id,
            "recipe_id": recipe.id,
            "tracking_type": "per_recipe",
            "percentage_left": 25.0,
            "description": "etwa ein Viertel",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["percentage_left"] == 25.0

    list_response = client.get(f"/leftovers/api/leftovers/camp/{camp.id}")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_leftover_delete_endpoint(client, db_session):
    camp = _make_camp(db_session)
    recipe = _make_recipe(db_session)
    leftover = crud.create_leftover(
        db_session,
        schemas.LeftoverCreate(
            camp_id=camp.id,
            recipe_id=recipe.id,
            tracking_type="per_recipe",
            percentage_left=10.0,
        ),
    )
    response = client.delete(f"/leftovers/api/leftovers/{leftover.id}")
    assert response.status_code == 200
    assert db_session.query(models.Leftover).count() == 0


# --- Story 8 follow-up: stats only count per_recipe entries ---


def test_statistics_ignores_per_ingredient_entries(db_session):
    """Per-ingredient measurements must not skew the per-recipe average (Story 8)."""
    recipe = _make_recipe(db_session)
    camp = _make_camp(db_session)
    ing = _make_ingredient(db_session)

    # Only per_ingredient data exists.
    crud.create_leftover(
        db_session,
        schemas.LeftoverCreate(
            camp_id=camp.id,
            recipe_id=recipe.id,
            ingredient_id=ing.id,
            tracking_type="per_ingredient",
            percentage_left=40.0,
        ),
    )

    stats = get_recipe_statistics(db_session, recipe.id, current_camp_id=camp.id)
    assert stats["total_entries"] == 0
    assert stats["avg_percentage_left"] is None
    assert stats["suggested_servings"] is None


def test_statistics_mixed_only_uses_per_recipe(db_session):
    recipe = _make_recipe(db_session)
    camp = _make_camp(db_session, participant_count=50)
    ing = _make_ingredient(db_session)

    crud.create_leftover(
        db_session,
        schemas.LeftoverCreate(
            camp_id=camp.id,
            recipe_id=recipe.id,
            tracking_type="per_recipe",
            percentage_left=20.0,
        ),
    )
    # Per-ingredient with much higher % should NOT inflate per-recipe avg.
    crud.create_leftover(
        db_session,
        schemas.LeftoverCreate(
            camp_id=camp.id,
            recipe_id=recipe.id,
            ingredient_id=ing.id,
            tracking_type="per_ingredient",
            percentage_left=80.0,
        ),
    )

    stats = get_recipe_statistics(db_session, recipe.id, current_camp_id=camp.id)
    assert stats["total_entries"] == 1
    assert stats["avg_percentage_left"] == pytest.approx(20.0)


# --- Story 7: sync endpoint replaces all entries for a meal plan ---


def _make_meal_plan(db_session, camp, recipe) -> models.MealPlan:
    mp = models.MealPlan(
        camp_id=camp.id,
        recipe_id=recipe.id,
        meal_date=datetime(2026, 7, 3),
        meal_type=models.MealType.LUNCH,
        position=0,
    )
    db_session.add(mp)
    db_session.commit()
    db_session.refresh(mp)
    return mp


def test_sync_endpoint_creates_combined_entries(client, db_session):
    camp = _make_camp(db_session)
    recipe = _make_recipe(db_session)
    ing_a = _make_ingredient(db_session, "Mehl")
    ing_b = _make_ingredient(db_session, "Butter")
    mp = _make_meal_plan(db_session, camp, recipe)

    client.cookies.set("current_camp_id", str(camp.id))
    response = client.post(
        f"/leftovers/api/meal-plan/{mp.id}/sync",
        json={
            "entries": [
                {"tracking_type": "per_recipe", "percentage_left": 20.0, "description": "ein Topf"},
                {"tracking_type": "per_ingredient", "ingredient_id": ing_a.id, "percentage_left": 30.0},
                {"tracking_type": "per_ingredient", "ingredient_id": ing_b.id, "percentage_left": 50.0},
            ]
        },
    )
    assert response.status_code == 200, response.text
    assert len(response.json()) == 3

    rows = crud.get_leftovers_for_meal_plan(db_session, mp.id)
    assert len(rows) == 3
    types = {(r.tracking_type, r.ingredient_id) for r in rows}
    assert ("per_recipe", None) in types
    assert ("per_ingredient", ing_a.id) in types
    assert ("per_ingredient", ing_b.id) in types


def test_sync_endpoint_replaces_previous_entries(client, db_session):
    camp = _make_camp(db_session)
    recipe = _make_recipe(db_session)
    ing_a = _make_ingredient(db_session, "Mehl")
    ing_b = _make_ingredient(db_session, "Butter")
    mp = _make_meal_plan(db_session, camp, recipe)
    client.cookies.set("current_camp_id", str(camp.id))

    # First sync: 3 entries.
    client.post(
        f"/leftovers/api/meal-plan/{mp.id}/sync",
        json={
            "entries": [
                {"tracking_type": "per_recipe", "percentage_left": 10.0},
                {"tracking_type": "per_ingredient", "ingredient_id": ing_a.id, "percentage_left": 20.0},
                {"tracking_type": "per_ingredient", "ingredient_id": ing_b.id, "percentage_left": 30.0},
            ]
        },
    )
    assert len(crud.get_leftovers_for_meal_plan(db_session, mp.id)) == 3

    # Second sync: only 1 entry — Mehl-only.
    response = client.post(
        f"/leftovers/api/meal-plan/{mp.id}/sync",
        json={
            "entries": [
                {"tracking_type": "per_ingredient", "ingredient_id": ing_a.id, "percentage_left": 50.0},
            ]
        },
    )
    assert response.status_code == 200
    rows = crud.get_leftovers_for_meal_plan(db_session, mp.id)
    assert len(rows) == 1
    assert rows[0].ingredient_id == ing_a.id
    assert rows[0].percentage_left == 50.0


def test_sync_endpoint_empty_list_clears_all(client, db_session):
    camp = _make_camp(db_session)
    recipe = _make_recipe(db_session)
    mp = _make_meal_plan(db_session, camp, recipe)
    client.cookies.set("current_camp_id", str(camp.id))

    client.post(
        f"/leftovers/api/meal-plan/{mp.id}/sync",
        json={"entries": [{"tracking_type": "per_recipe", "percentage_left": 25.0}]},
    )
    assert len(crud.get_leftovers_for_meal_plan(db_session, mp.id)) == 1

    response = client.post(f"/leftovers/api/meal-plan/{mp.id}/sync", json={"entries": []})
    assert response.status_code == 200
    assert len(crud.get_leftovers_for_meal_plan(db_session, mp.id)) == 0


def test_sync_endpoint_rejects_per_ingredient_without_ingredient_id(client, db_session):
    camp = _make_camp(db_session)
    recipe = _make_recipe(db_session)
    mp = _make_meal_plan(db_session, camp, recipe)
    client.cookies.set("current_camp_id", str(camp.id))

    response = client.post(
        f"/leftovers/api/meal-plan/{mp.id}/sync",
        json={
            "entries": [
                {"tracking_type": "per_ingredient", "percentage_left": 10.0},
            ]
        },
    )
    assert response.status_code == 422  # Pydantic validation error
