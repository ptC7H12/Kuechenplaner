"""Tests for daily-lists and recipe-book PDF export."""

import base64
import contextlib
import re
import zlib
from datetime import datetime

import pytest

from app import crud, models, schemas


def _pdf_text(content: bytes) -> str:
    """Decode the ASCII85 + Flate streams of a ReportLab PDF so tests can assert on
    the rendered text without an external PDF library."""
    text = []
    for match in re.finditer(rb"stream\r?\n(.*?)endstream", content, re.DOTALL):
        data = match.group(1).strip(b"\r\n")
        if data.endswith(b"~>"):
            with contextlib.suppress(ValueError):
                data = base64.a85decode(data[:-2])
        try:
            data = zlib.decompress(data)
        except zlib.error:
            continue
        text.append(data.decode("latin-1", "replace"))
    return "".join(text)


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
    ing = models.Ingredient(name=f"Zutat-{name}", unit="g")
    db_session.add(ing)
    db_session.flush()
    recipe = models.Recipe(
        name=name,
        base_servings=10,
        instructions="1. Anbraten.\n2. Schmoren.\n3. Servieren.",
    )
    db_session.add(recipe)
    db_session.flush()
    db_session.add(models.RecipeIngredient(recipe_id=recipe.id, ingredient_id=ing.id, quantity=300, unit="g"))
    db_session.commit()
    db_session.refresh(recipe)
    return recipe


def _tag_recipe(db_session, recipe, tag_name="Vegan", allergen_name="Nuss"):
    """Attach an ASCII-named tag and allergen so they appear literally in the
    uncompressed PDF stream."""
    tag = models.Tag(name=tag_name, color="#22C55E")
    allergen = models.Allergen(name=allergen_name)
    db_session.add_all([tag, allergen])
    db_session.flush()
    recipe.tags.append(tag)
    recipe.allergens.append(allergen)
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

    _add_meal_plan(db_session, camp.id, starter.id, models.MealType.DINNER, sub_category="Vorspeise", position=0)
    _add_meal_plan(db_session, camp.id, main.id, models.MealType.DINNER, sub_category="Hauptgang", position=1)

    response = client.get(f"/export/daily-lists/pdf/{camp.id}")
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


@pytest.mark.parametrize("path_segment", ["daily-lists", "recipe-book"])
def test_pdf_includes_tags_and_allergens(client, db_session, path_segment):
    camp = _make_camp(db_session)
    recipe = _make_recipe(db_session)
    _tag_recipe(db_session, recipe)
    _add_meal_plan(db_session, camp.id, recipe.id, models.MealType.LUNCH)

    response = client.get(f"/export/{path_segment}/pdf/{camp.id}")
    assert response.status_code == 200
    text = _pdf_text(response.content)
    assert "Vegan" in text
    assert "Nuss" in text
