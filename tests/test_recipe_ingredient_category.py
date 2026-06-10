"""Tests for Story 39: editing an ingredient's category from the recipe form.

Covers that the create/update recipe endpoints persist a per-ingredient
``category_id`` onto the *global* ``Ingredient`` row (via ``update_ingredient``)
and that the change is afterwards visible in the fuzzy ingredient search.
"""

from __future__ import annotations

import json

from app import crud, schemas


def _category(db, name, color="#112233"):
    return crud.create_category(db, schemas.CategoryCreate(name=name, color=color))


def test_create_recipe_updates_global_ingredient_category(client, db_session):
    _category(db_session, "Sonstiges")
    new_category = _category(db_session, "Gemüse", color="#22C55E")
    ingredient = crud.get_or_create_ingredient(db_session, name="Karotte", unit="g", category="Sonstiges")
    assert ingredient.category.name == "Sonstiges"

    response = client.post(
        "/recipes/",
        data={
            "name": "Eintopf",
            "base_servings": 10,
            "instructions": "Kochen.",
            "ingredients": json.dumps(
                [{"ingredient_id": ingredient.id, "quantity": 500, "unit": "g", "category_id": new_category.id}]
            ),
            "tag_ids": "[]",
            "allergen_ids": "[]",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    db_session.expire_all()
    refreshed = crud.get_ingredient(db_session, ingredient.id)
    assert refreshed.category_id == new_category.id


def test_update_recipe_changes_global_ingredient_category(client, db_session):
    _category(db_session, "Sonstiges")
    new_category = _category(db_session, "Milchprodukte", color="#60A5FA")
    ingredient = crud.get_or_create_ingredient(db_session, name="Butter", unit="g", category="Sonstiges")

    recipe = crud.create_recipe(
        db_session,
        schemas.RecipeCreate(
            name="Kuchen",
            base_servings=10,
            ingredients=[schemas.RecipeIngredientCreate(ingredient_id=ingredient.id, quantity=100, unit="g")],
        ),
    )

    response = client.put(
        f"/recipes/{recipe.id}",
        data={
            "name": "Kuchen",
            "base_servings": 10,
            "instructions": "Backen.",
            "ingredients": json.dumps(
                [{"ingredient_id": ingredient.id, "quantity": 100, "unit": "g", "category_id": new_category.id}]
            ),
            "tag_ids": "[]",
            "allergen_ids": "[]",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    db_session.expire_all()
    refreshed = crud.get_ingredient(db_session, ingredient.id)
    assert refreshed.category_id == new_category.id


def test_category_change_is_visible_in_fuzzy_search(client, db_session):
    _category(db_session, "Sonstiges")
    new_category = _category(db_session, "Gewürze", color="#F59E0B")
    ingredient = crud.get_or_create_ingredient(db_session, name="Pfeffer", unit="g", category="Sonstiges")

    client.post(
        "/recipes/",
        data={
            "name": "Würzmischung",
            "base_servings": 5,
            "instructions": "Mischen.",
            "ingredients": json.dumps(
                [{"ingredient_id": ingredient.id, "quantity": 10, "unit": "g", "category_id": new_category.id}]
            ),
            "tag_ids": "[]",
            "allergen_ids": "[]",
        },
        follow_redirects=False,
    )

    response = client.get("/recipes/api/ingredients/search?q=Pfeffer")
    assert response.status_code == 200
    results = response.json()
    assert results[0]["category"] == "Gewürze"
    assert results[0]["category_id"] == new_category.id


def test_recipe_without_category_id_still_works(client, db_session):
    ingredient = crud.get_or_create_ingredient(db_session, name="Salz", unit="g", category="Sonstiges")

    response = client.post(
        "/recipes/",
        data={
            "name": "Salzwasser",
            "base_servings": 4,
            "instructions": "Lösen.",
            "ingredients": json.dumps([{"ingredient_id": ingredient.id, "quantity": 5, "unit": "g"}]),
            "tag_ids": "[]",
            "allergen_ids": "[]",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
