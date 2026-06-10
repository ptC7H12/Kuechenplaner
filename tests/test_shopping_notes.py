"""Tests for Story 2: global ingredient notes + camp-specific shopping list notes."""

from datetime import datetime

from app import crud, models, schemas
from app.services.calculation import calculate_shopping_list


def _make_camp(db_session, name: str = "Camp", participant_count: int = 10):
    return crud.create_camp(
        db_session,
        schemas.CampCreate(
            name=name,
            start_date=datetime(2026, 7, 1),
            end_date=datetime(2026, 7, 7),
            participant_count=participant_count,
        ),
    )


def _make_ingredient(db_session, name: str = "Mehl") -> models.Ingredient:
    ing = models.Ingredient(name=name, unit="g")
    db_session.add(ing)
    db_session.commit()
    db_session.refresh(ing)
    return ing


def _make_recipe_with_ingredient(db_session, ingredient: models.Ingredient) -> models.Recipe:
    recipe = models.Recipe(name="Brot", base_servings=10)
    db_session.add(recipe)
    db_session.flush()
    ri = models.RecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=ingredient.id,
        quantity=500,
        unit="g",
    )
    db_session.add(ri)
    db_session.commit()
    db_session.refresh(recipe)
    return recipe


def _add_meal_plan(db_session, camp_id: int, recipe_id: int) -> models.MealPlan:
    mp = models.MealPlan(
        camp_id=camp_id,
        recipe_id=recipe_id,
        meal_date=datetime(2026, 7, 2),
        meal_type=models.MealType.LUNCH,
        position=0,
    )
    db_session.add(mp)
    db_session.commit()
    return mp


def test_upsert_note_creates_then_updates(db_session):
    camp = _make_camp(db_session)
    ing = _make_ingredient(db_session)

    saved = crud.upsert_shopping_list_note(db_session, camp.id, ing.id, "frisch kaufen")
    assert saved is not None
    assert saved.note == "frisch kaufen"

    updated = crud.upsert_shopping_list_note(db_session, camp.id, ing.id, "lieber tiefgekühlt")
    assert updated.id == saved.id
    assert updated.note == "lieber tiefgekühlt"


def test_upsert_empty_note_deletes_existing(db_session):
    camp = _make_camp(db_session)
    ing = _make_ingredient(db_session)
    crud.upsert_shopping_list_note(db_session, camp.id, ing.id, "wird gleich gelöscht")

    result = crud.upsert_shopping_list_note(db_session, camp.id, ing.id, "")
    assert result is None
    assert crud.get_shopping_list_note(db_session, camp.id, ing.id) is None


def test_update_ingredient_note_sets_global_note(db_session):
    ing = _make_ingredient(db_session)
    updated = crud.update_ingredient_note(db_session, ing.id, "beim Großhändler bestellen")
    assert updated.note == "beim Großhändler bestellen"

    cleared = crud.update_ingredient_note(db_session, ing.id, "   ")
    assert cleared.note is None


def test_calculate_shopping_list_includes_both_notes(db_session):
    camp = _make_camp(db_session)
    ing = _make_ingredient(db_session)
    recipe = _make_recipe_with_ingredient(db_session, ing)
    _add_meal_plan(db_session, camp.id, recipe.id)

    crud.update_ingredient_note(db_session, ing.id, "global: Bio-Variante")
    crud.upsert_shopping_list_note(db_session, camp.id, ing.id, "camp: lokal kaufen")

    result = calculate_shopping_list(db_session, camp.id)
    items = result["items"]
    assert len(items) == 1
    item = items[0]
    assert item["global_note"] == "global: Bio-Variante"
    assert item["note"] == "camp: lokal kaufen"


def test_camp_notes_are_isolated_per_camp(db_session):
    camp_a = _make_camp(db_session, "A")
    camp_b = _make_camp(db_session, "B")
    ing = _make_ingredient(db_session)
    recipe = _make_recipe_with_ingredient(db_session, ing)
    _add_meal_plan(db_session, camp_a.id, recipe.id)
    _add_meal_plan(db_session, camp_b.id, recipe.id)

    crud.upsert_shopping_list_note(db_session, camp_a.id, ing.id, "Notiz nur fuer A")

    items_a = calculate_shopping_list(db_session, camp_a.id)["items"]
    items_b = calculate_shopping_list(db_session, camp_b.id)["items"]
    assert items_a[0]["note"] == "Notiz nur fuer A"
    assert items_b[0]["note"] is None
