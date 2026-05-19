"""Tests for Story 26: shopping-list aggregation.

The shopping list must collapse:
  - ingredient rows that differ only in case/whitespace
    (e.g. "Hackfleisch" vs. "hackfleisch "),
  - the *same* ingredient referenced with compatible mass/volume units
    (g + kg → one row in kg, ml + L → one row in L).

Units of different dimensions (g vs. EL, ml vs. Stück) must stay on
separate rows. Notes from each contributing Ingredient row are joined
with "; " and deduplicated.
"""

from datetime import datetime

import pytest

from app import crud, models, schemas
from app.services.calculation import calculate_shopping_list


def _make_camp(db_session, participant_count: int = 10) -> models.Camp:
    return crud.create_camp(
        db_session,
        schemas.CampCreate(
            name="Camp Aggregation",
            start_date=datetime(2026, 7, 1),
            end_date=datetime(2026, 7, 7),
            participant_count=participant_count,
        ),
    )


def _make_ingredient(db_session, name: str, *, unit: str = "kg",
                     category: str = "Fleisch", note: str | None = None) -> models.Ingredient:
    ing = models.Ingredient(name=name, unit=unit, category=category, note=note)
    db_session.add(ing)
    db_session.flush()
    return ing


def _make_recipe_with(db_session, ingredient: models.Ingredient,
                      quantity: float, unit: str,
                      recipe_name: str = "Spaghetti Bolognese",
                      base_servings: int = 10) -> models.Recipe:
    recipe = models.Recipe(name=recipe_name, base_servings=base_servings)
    db_session.add(recipe)
    db_session.flush()
    db_session.add(models.RecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=ingredient.id,
        quantity=quantity,
        unit=unit,
    ))
    db_session.commit()
    db_session.refresh(recipe)
    return recipe


def _add_meal_plan(db_session, camp_id: int, recipe_id: int, position: int = 0):
    mp = models.MealPlan(
        camp_id=camp_id,
        recipe_id=recipe_id,
        meal_date=datetime(2026, 7, 2),
        meal_type=models.MealType.LUNCH,
        position=position,
    )
    db_session.add(mp)
    db_session.commit()


def test_duplicate_ingredient_rows_collapse_into_one_line(db_session):
    """Two Ingredient rows with the same normalised name + unit produce one
    shopping-list row whose quantity is the sum of both."""
    camp = _make_camp(db_session)
    # Two DB rows the UNIQUE("name") constraint sees as distinct (case/whitespace).
    ing_a = _make_ingredient(db_session, "Hackfleisch")
    ing_b = _make_ingredient(db_session, "hackfleisch ")
    recipe_a = _make_recipe_with(db_session, ing_a, quantity=1.0, unit="kg",
                                 recipe_name="Lasagne")
    recipe_b = _make_recipe_with(db_session, ing_b, quantity=3.3, unit="kg",
                                 recipe_name="Chili")
    _add_meal_plan(db_session, camp.id, recipe_a.id, position=0)
    _add_meal_plan(db_session, camp.id, recipe_b.id, position=1)

    result = calculate_shopping_list(db_session, camp.id)
    items = result["items"]
    assert len(items) == 1, f"expected one collapsed row, got {len(items)}"
    item = items[0]
    # Aggregation runs in base units (g); convert_unit re-promotes to kg.
    assert item["quantity"] == pytest.approx(4.3)
    assert item["unit"] == "kg"
    # Display name uses the first-seen Ingredient row (stable for textarea binding).
    assert item["ingredient"].name == "Hackfleisch"


def test_mass_units_collapse_into_one_line(db_session):
    """Same ingredient with g in one recipe and kg in another produces a
    single shopping-list row, with the quantity summed in the display unit."""
    camp = _make_camp(db_session)
    ing = _make_ingredient(db_session, "Hackfleisch")
    recipe_g = _make_recipe_with(db_session, ing, quantity=500, unit="g",
                                 recipe_name="Gratin")
    recipe_kg = _make_recipe_with(db_session, ing, quantity=2.0, unit="kg",
                                  recipe_name="Bolognese")
    _add_meal_plan(db_session, camp.id, recipe_g.id, position=0)
    _add_meal_plan(db_session, camp.id, recipe_kg.id, position=1)

    result = calculate_shopping_list(db_session, camp.id)
    items = result["items"]
    assert len(items) == 1
    item = items[0]
    # 500 g + 2000 g = 2500 g → 2.5 kg after display conversion.
    assert item["quantity"] == pytest.approx(2.5)
    assert item["unit"] == "kg"


def test_volume_units_collapse_into_one_line(db_session):
    """ml + L for the same ingredient collapse to a single row in L."""
    camp = _make_camp(db_session)
    ing = _make_ingredient(db_session, "Apfelsaft", unit="ml", category="Getränke")
    recipe_ml = _make_recipe_with(db_session, ing, quantity=800, unit="ml",
                                  recipe_name="Punsch")
    recipe_l = _make_recipe_with(db_session, ing, quantity=1.0, unit="L",
                                 recipe_name="Saftmix")
    _add_meal_plan(db_session, camp.id, recipe_ml.id, position=0)
    _add_meal_plan(db_session, camp.id, recipe_l.id, position=1)

    result = calculate_shopping_list(db_session, camp.id)
    items = result["items"]
    assert len(items) == 1
    item = items[0]
    # 800 ml + 1000 ml = 1800 ml → 1.8 L.
    assert item["quantity"] == pytest.approx(1.8)
    assert item["unit"] == "L"


def test_mehl_g_kg_el_yields_two_lines(db_session):
    """Mehl in g + kg collapses to one kg row; the EL entry stays a second row."""
    camp = _make_camp(db_session)
    ing = _make_ingredient(db_session, "Mehl", unit="g", category="Backwaren")
    recipe_g = _make_recipe_with(db_session, ing, quantity=900, unit="g",
                                 recipe_name="Fladenbrot")
    recipe_kg = _make_recipe_with(db_session, ing, quantity=1.5, unit="kg",
                                  recipe_name="Pizzateig")
    recipe_el = _make_recipe_with(db_session, ing, quantity=8, unit="EL",
                                  recipe_name="Apple crumble")
    _add_meal_plan(db_session, camp.id, recipe_g.id, position=0)
    _add_meal_plan(db_session, camp.id, recipe_kg.id, position=1)
    _add_meal_plan(db_session, camp.id, recipe_el.id, position=2)

    result = calculate_shopping_list(db_session, camp.id)
    items = sorted(result["items"], key=lambda it: it["unit"])
    assert len(items) == 2, f"expected EL + kg, got {[it['unit'] for it in items]}"
    units = {it["unit"]: it["quantity"] for it in items}
    assert units["EL"] == pytest.approx(8)
    # 900 g + 1500 g = 2400 g → 2.4 kg.
    assert units["kg"] == pytest.approx(2.4)


def test_single_unit_aggregation_unchanged(db_session):
    """Two recipes both using "Stück" still aggregate into one row — regression
    guard for the non-metric path through normalize_to_base."""
    camp = _make_camp(db_session)
    ing = _make_ingredient(db_session, "Apfel", unit="Stück", category="Obst")
    recipe_a = _make_recipe_with(db_session, ing, quantity=5, unit="Stück",
                                 recipe_name="Apfelsalat")
    recipe_b = _make_recipe_with(db_session, ing, quantity=3, unit="Stück",
                                 recipe_name="Apfelmus")
    _add_meal_plan(db_session, camp.id, recipe_a.id, position=0)
    _add_meal_plan(db_session, camp.id, recipe_b.id, position=1)

    result = calculate_shopping_list(db_session, camp.id)
    items = result["items"]
    assert len(items) == 1
    assert items[0]["unit"] == "Stück"
    assert items[0]["quantity"] == 8


def test_different_units_do_not_collapse(db_session):
    """Same name but different units must stay on separate rows (regression
    guard — see story-26 Backwaren "Zucker" example)."""
    camp = _make_camp(db_session)
    ing_a = _make_ingredient(db_session, "Zucker", unit="EL", category="Backwaren")
    ing_b = _make_ingredient(db_session, "Zucker ", unit="g", category="Backwaren")
    recipe_a = _make_recipe_with(db_session, ing_a, quantity=10.0, unit="EL",
                                 recipe_name="Kuchen")
    recipe_b = _make_recipe_with(db_session, ing_b, quantity=200.0, unit="g",
                                 recipe_name="Pudding")
    _add_meal_plan(db_session, camp.id, recipe_a.id, position=0)
    _add_meal_plan(db_session, camp.id, recipe_b.id, position=1)

    result = calculate_shopping_list(db_session, camp.id)
    items = result["items"]
    assert len(items) == 2


def test_notes_are_merged_across_duplicates(db_session):
    """Global notes from each duplicate Ingredient row are joined with '; ';
    camp notes attached to either ingredient_id flow into the merged row."""
    camp = _make_camp(db_session)
    ing_a = _make_ingredient(db_session, "Mehl", unit="g", category="Backwaren",
                             note="Bio-Variante")
    ing_b = _make_ingredient(db_session, "mehl", unit="g", category="Backwaren",
                             note="beim Großhändler bestellen")
    recipe_a = _make_recipe_with(db_session, ing_a, quantity=500, unit="g",
                                 recipe_name="Brot")
    recipe_b = _make_recipe_with(db_session, ing_b, quantity=300, unit="g",
                                 recipe_name="Kuchen")
    _add_meal_plan(db_session, camp.id, recipe_a.id, position=0)
    _add_meal_plan(db_session, camp.id, recipe_b.id, position=1)

    crud.upsert_shopping_list_note(db_session, camp.id, ing_b.id, "lokal kaufen")

    result = calculate_shopping_list(db_session, camp.id)
    items = result["items"]
    assert len(items) == 1
    item = items[0]
    assert item["global_note"] == "Bio-Variante; beim Großhändler bestellen"
    assert item["note"] == "lokal kaufen"


def test_duplicate_notes_are_deduplicated(db_session):
    """Identical notes on both duplicates appear only once after the merge."""
    camp = _make_camp(db_session)
    ing_a = _make_ingredient(db_session, "Salz", unit="g", category="Gewürze",
                             note="grobes Meersalz")
    ing_b = _make_ingredient(db_session, "salz ", unit="g", category="Gewürze",
                             note="grobes Meersalz")
    recipe_a = _make_recipe_with(db_session, ing_a, quantity=20, unit="g",
                                 recipe_name="Suppe")
    recipe_b = _make_recipe_with(db_session, ing_b, quantity=30, unit="g",
                                 recipe_name="Eintopf")
    _add_meal_plan(db_session, camp.id, recipe_a.id, position=0)
    _add_meal_plan(db_session, camp.id, recipe_b.id, position=1)

    result = calculate_shopping_list(db_session, camp.id)
    assert result["items"][0]["global_note"] == "grobes Meersalz"
