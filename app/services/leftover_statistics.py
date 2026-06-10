"""Aggregated leftover statistics per recipe across all camps."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app import models


def get_recipe_statistics(db: Session, recipe_id: int, current_camp_id: int | None = None) -> dict:
    """Compute "per recipe" leftover statistics for a single recipe across all camps.

    Only `tracking_type == 'per_recipe'` entries flow into this aggregate so that
    per-ingredient measurements don't distort the recipe-level skip suggestion.
    Per-ingredient data is surfaced via `get_ingredient_breakdown()` instead.
    """
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        return {
            "recipe_id": recipe_id,
            "recipe_name": None,
            "total_entries": 0,
            "camps_with_leftovers": 0,
            "avg_percentage_left": None,
            "suggested_servings": None,
            "base_camp_participants": None,
        }

    entries = (
        db.query(models.Leftover)
        .filter(
            models.Leftover.recipe_id == recipe_id,
            models.Leftover.tracking_type == "per_recipe",
        )
        .all()
    )
    with_pct = [e for e in entries if e.percentage_left is not None]

    avg_pct: float | None = None
    if with_pct:
        avg_pct = sum(e.percentage_left for e in with_pct) / len(with_pct)

    camps_with_leftovers = len({e.camp_id for e in with_pct if e.percentage_left and e.percentage_left > 0})

    suggested = None
    base_participants = None
    if current_camp_id is not None and avg_pct is not None and avg_pct > 10:
        camp = db.query(models.Camp).filter(models.Camp.id == current_camp_id).first()
        if camp:
            base_participants = camp.participant_count
            suggested = max(1, round(camp.participant_count * (1 - avg_pct / 100)))

    return {
        "recipe_id": recipe_id,
        "recipe_name": recipe.name,
        "total_entries": len(entries),
        "camps_with_leftovers": camps_with_leftovers,
        "avg_percentage_left": avg_pct,
        "suggested_servings": suggested,
        "base_camp_participants": base_participants,
    }


def get_ingredient_breakdown(db: Session, recipe_id: int) -> list[dict]:
    """Aggregate per-ingredient leftovers across all camps for a recipe.

    Returns a list of {ingredient_id, ingredient_name, avg_percentage_left, camps_count}.
    Only entries with tracking_type='per_ingredient' and a non-null ingredient_id
    contribute. Ingredients without leftover data are omitted.
    """
    entries = (
        db.query(models.Leftover)
        .filter(
            models.Leftover.recipe_id == recipe_id,
            models.Leftover.tracking_type == "per_ingredient",
            models.Leftover.ingredient_id.isnot(None),
        )
        .all()
    )

    grouped: dict[int, list] = {}
    camps_by_ingredient: dict[int, set] = {}
    for e in entries:
        grouped.setdefault(e.ingredient_id, []).append(e)
        if e.percentage_left and e.percentage_left > 0:
            camps_by_ingredient.setdefault(e.ingredient_id, set()).add(e.camp_id)

    breakdown = []
    for ingredient_id, items in grouped.items():
        ingredient = db.query(models.Ingredient).filter(models.Ingredient.id == ingredient_id).first()
        with_pct = [i for i in items if i.percentage_left is not None]
        avg = sum(i.percentage_left for i in with_pct) / len(with_pct) if with_pct else None
        breakdown.append(
            {
                "ingredient_id": ingredient_id,
                "ingredient_name": ingredient.name if ingredient else f"#{ingredient_id}",
                "avg_percentage_left": avg,
                "camps_count": len(camps_by_ingredient.get(ingredient_id, set())),
            }
        )

    breakdown.sort(key=lambda b: b["avg_percentage_left"] or 0, reverse=True)
    return breakdown


def count_recipe_leftover_entries(db: Session, recipe_id: int) -> int:
    """Total number of Leftover rows for a recipe (both tracking_types)."""
    return db.query(models.Leftover).filter(models.Leftover.recipe_id == recipe_id).count()
