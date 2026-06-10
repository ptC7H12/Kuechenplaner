"""Tests for Story 30: manual ingredient categories.

Covers the `update_ingredient` CRUD helper plus the category create/delete and
ingredient PATCH endpoints in the settings router.
"""

from __future__ import annotations

from app import crud, schemas


def _make_ingredient(db, name="Mehl", unit="g", category="Backwaren"):
    return crud.get_or_create_ingredient(db, name=name, unit=unit, category=category)


def test_get_or_create_ingredient_resolves_category(db_session):
    ingredient = _make_ingredient(db_session)
    assert ingredient.category is not None
    assert ingredient.category.name == "Backwaren"

    # Same category name reuses the existing row.
    other = crud.get_or_create_ingredient(db_session, name="Zucker", unit="g", category="Backwaren")
    assert other.category_id == ingredient.category_id


def test_update_ingredient_changes_category_and_unit(db_session):
    ingredient = _make_ingredient(db_session)
    new_category = crud.create_category(db_session, schemas.CategoryCreate(name="Tiefkühl", color="#123456"))

    updated = crud.update_ingredient(
        db_session,
        ingredient.id,
        schemas.IngredientUpdate(category_id=new_category.id, unit="kg"),
    )

    assert updated.category_id == new_category.id
    assert updated.unit == "kg"


def test_update_ingredient_can_clear_category(db_session):
    ingredient = _make_ingredient(db_session)

    updated = crud.update_ingredient(
        db_session,
        ingredient.id,
        schemas.IngredientUpdate(category_id=None),
    )

    assert updated.category_id is None


def test_create_category_endpoint(client, db_session):
    response = client.post("/settings/api/categories", data={"name": "Tiefkühl", "color": "#0EA5E9"})

    assert response.status_code == 201
    assert "Tiefkühl" in response.text

    db_session.expire_all()
    assert crud.get_category_by_name(db_session, "Tiefkühl") is not None


def test_create_category_rejects_empty_name(client, db_session):
    response = client.post("/settings/api/categories", data={"name": "   ", "color": "#0EA5E9"})

    assert response.status_code == 422
    db_session.expire_all()
    assert crud.get_categories(db_session) == []


def test_create_category_rejects_duplicate(client, db_session):
    crud.create_category(db_session, schemas.CategoryCreate(name="Tiefkühl"))

    response = client.post("/settings/api/categories", data={"name": "Tiefkühl"})

    assert response.status_code == 400


def test_delete_category_nulls_ingredient_reference(client, db_session):
    ingredient = _make_ingredient(db_session)
    category_id = ingredient.category_id

    response = client.delete(f"/settings/api/categories/{category_id}")

    assert response.status_code == 200
    db_session.expire_all()
    assert crud.get_category(db_session, category_id) is None
    assert crud.get_ingredient(db_session, ingredient.id).category_id is None


def test_patch_ingredient_endpoint_updates_row(client, db_session):
    ingredient = _make_ingredient(db_session)
    new_category = crud.create_category(db_session, schemas.CategoryCreate(name="Tiefkühl"))

    response = client.patch(
        f"/settings/ingredients/{ingredient.id}",
        data={"category_id": str(new_category.id), "unit": "kg"},
    )

    assert response.status_code == 200
    assert "Mehl" in response.text

    db_session.expire_all()
    refreshed = crud.get_ingredient(db_session, ingredient.id)
    assert refreshed.category_id == new_category.id
    assert refreshed.unit == "kg"


def test_patch_ingredient_unknown_id_returns_404(client):
    response = client.patch("/settings/ingredients/999999", data={"category_id": ""})
    assert response.status_code == 404
