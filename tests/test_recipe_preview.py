"""Tests for Story 4: recipe-preview modal HTML fragment endpoint."""

from app import crud, models, schemas


def _make_recipe(db_session) -> models.Recipe:
    ing = models.Ingredient(name="Mehl", unit="g")
    db_session.add(ing)
    db_session.flush()

    recipe = models.Recipe(
        name="Pizza Margherita",
        description="Klassische italienische Pizza",
        base_servings=4,
        instructions="1. Teig kneten.\n2. Belegen.\n3. Backen.",
        preparation_time=20,
        cooking_time=15,
    )
    db_session.add(recipe)
    db_session.flush()
    db_session.add(
        models.RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ing.id,
            quantity=400,
            unit="g",
        )
    )
    db_session.commit()
    db_session.refresh(recipe)
    return recipe


def _make_camp(db_session, participant_count: int = 12) -> models.Camp:
    from datetime import datetime

    return crud.create_camp(
        db_session,
        schemas.CampCreate(
            name="Camp Preview",
            start_date=datetime(2026, 7, 1),
            end_date=datetime(2026, 7, 7),
            participant_count=participant_count,
        ),
    )


def test_preview_returns_html_fragment_with_recipe(client, db_session):
    recipe = _make_recipe(db_session)
    # Preview endpoints need a current camp in context for base.html.
    camp = _make_camp(db_session)
    client.cookies.set("current_camp_id", str(camp.id))

    response = client.get(f"/recipes/{recipe.id}/preview")
    assert response.status_code == 200
    body = response.text
    assert "Pizza Margherita" in body
    assert "Mehl" in body
    assert "Teig kneten" in body


def test_preview_scales_to_servings_query_param(client, db_session):
    recipe = _make_recipe(db_session)  # base 4 servings, 400 g Mehl
    camp = _make_camp(db_session)
    client.cookies.set("current_camp_id", str(camp.id))

    response = client.get(f"/recipes/{recipe.id}/preview?servings=12")
    assert response.status_code == 200
    # Scaling factor = 12 / 4 = 3 → 1200 g
    assert "1200.0 g" in response.text
    assert "12" in response.text  # target servings shown in header


def test_preview_uses_base_servings_when_servings_missing(client, db_session):
    recipe = _make_recipe(db_session)
    camp = _make_camp(db_session)
    client.cookies.set("current_camp_id", str(camp.id))

    response = client.get(f"/recipes/{recipe.id}/preview")
    assert response.status_code == 200
    # No scaling: ingredient stays at 400 g
    assert "400.0 g" in response.text


def test_preview_404_when_recipe_missing(client, db_session):
    camp = _make_camp(db_session)
    client.cookies.set("current_camp_id", str(camp.id))

    response = client.get("/recipes/99999/preview")
    assert response.status_code == 404
