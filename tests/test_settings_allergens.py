"""Tests for Story 33: managing allergens in the settings UI.

Covers the `delete_allergen` CRUD helper plus the allergen create/delete
endpoints in the settings router (including M:N cleanup on delete).
"""

from __future__ import annotations

from app import crud, models, schemas


def _make_recipe_with_allergen(db, allergen_name="Gluten"):
    allergen = crud.create_allergen(db, schemas.AllergenCreate(name=allergen_name, icon="🌾"))
    recipe = models.Recipe(name="Brot", base_servings=10)
    recipe.allergens.append(allergen)
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    db.refresh(allergen)
    return recipe, allergen


def test_create_allergen_endpoint(client, db_session):
    response = client.post("/settings/api/allergens", data={"name": "Laktose", "icon": "🥛"})

    assert response.status_code == 201
    assert "Laktose" in response.text

    db_session.expire_all()
    assert crud.get_allergen_by_name(db_session, "Laktose") is not None


def test_create_allergen_rejects_empty_name(client, db_session):
    response = client.post("/settings/api/allergens", data={"name": "   "})

    assert response.status_code == 422
    db_session.expire_all()
    assert crud.get_allergens(db_session) == []


def test_create_allergen_rejects_duplicate(client, db_session):
    crud.create_allergen(db_session, schemas.AllergenCreate(name="Gluten"))

    response = client.post("/settings/api/allergens", data={"name": "Gluten"})

    assert response.status_code == 400


def test_delete_allergen_removes_recipe_link(client, db_session):
    recipe, allergen = _make_recipe_with_allergen(db_session)
    recipe_id, allergen_id = recipe.id, allergen.id

    response = client.delete(f"/settings/api/allergens/{allergen_id}")

    assert response.status_code == 200
    db_session.expire_all()
    assert crud.get_allergen(db_session, allergen_id) is None
    # Recipe survives, but the M:N link is gone.
    refreshed = crud.get_recipe(db_session, recipe_id)
    assert refreshed is not None
    assert refreshed.allergens == []


def test_delete_allergen_unknown_id_returns_404(client):
    response = client.delete("/settings/api/allergens/999999")
    assert response.status_code == 404
