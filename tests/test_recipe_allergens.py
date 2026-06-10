"""Tests for Story 35: selecting allergens structurally in the recipe form.

Covers that the create/update recipe endpoints persist `allergen_ids` into the
M:N relation and that the detail page renders the structured allergen names.
"""

from __future__ import annotations

import json

from app import crud, schemas


def _make_allergen(db, name, icon="🌾"):
    return crud.create_allergen(db, schemas.AllergenCreate(name=name, icon=icon))


def test_create_recipe_persists_allergen_ids(client, db_session):
    gluten = _make_allergen(db_session, "Gluten")
    laktose = _make_allergen(db_session, "Laktose", icon="🥛")

    response = client.post(
        "/recipes/",
        data={
            "name": "Pizza",
            "base_servings": 10,
            "instructions": "Backen.",
            "ingredients": "[]",
            "tag_ids": "[]",
            "allergen_ids": json.dumps([gluten.id, laktose.id]),
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    db_session.expire_all()
    recipes = crud.get_recipes(db_session)
    assert len(recipes) == 1
    allergen_ids = {a.id for a in recipes[0].allergens}
    assert allergen_ids == {gluten.id, laktose.id}


def test_update_recipe_replaces_allergen_ids(client, db_session):
    gluten = _make_allergen(db_session, "Gluten")
    laktose = _make_allergen(db_session, "Laktose", icon="🥛")

    recipe = crud.create_recipe(
        db_session,
        schemas.RecipeCreate(name="Brot", base_servings=10, allergen_ids=[gluten.id]),
    )
    recipe_id = recipe.id

    response = client.put(
        f"/recipes/{recipe_id}",
        data={
            "name": "Brot",
            "base_servings": 10,
            "instructions": "Backen.",
            "ingredients": "[]",
            "tag_ids": "[]",
            "allergen_ids": json.dumps([laktose.id]),
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    db_session.expire_all()
    refreshed = crud.get_recipe(db_session, recipe_id)
    assert {a.id for a in refreshed.allergens} == {laktose.id}


def test_detail_page_shows_structured_allergens(client, db_session):
    gluten = _make_allergen(db_session, "Gluten")
    recipe = crud.create_recipe(
        db_session,
        schemas.RecipeCreate(name="Brot", base_servings=10, allergen_ids=[gluten.id]),
    )

    response = client.get(f"/recipes/{recipe.id}")

    assert response.status_code == 200
    assert "Gluten" in response.text
