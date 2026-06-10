"""Leftover tracker: record what was left over after a meal, view per-camp
overview and per-recipe statistics across all camps."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_camp, get_template_context, templates
from app.logging_config import get_logger
from app.services.leftover_statistics import get_ingredient_breakdown, get_recipe_statistics

logger = get_logger("leftovers")

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def leftovers_index(
    request: Request,
    context: dict = Depends(get_template_context),
    current_camp: models.Camp = Depends(get_current_camp),
    db: Session = Depends(get_db),
):
    if not current_camp:
        return templates.TemplateResponse("meal_planning/no_camp.html", context)

    leftovers = crud.get_leftovers_for_camp(db, current_camp.id)

    pct_values = [lo.percentage_left for lo in leftovers if lo.percentage_left is not None]
    avg_pct = sum(pct_values) / len(pct_values) if pct_values else None
    recipes_with_leftovers = len({lo.recipe_id for lo in leftovers if lo.recipe_id is not None})

    context.update(
        {
            "camp": current_camp,
            "leftovers": leftovers,
            "total_entries": len(leftovers),
            "avg_pct": avg_pct,
            "recipes_with_leftovers": recipes_with_leftovers,
        }
    )
    return templates.TemplateResponse("leftovers/index.html", context)


@router.get("/new", response_class=HTMLResponse)
async def leftovers_new_modal(
    request: Request,
    meal_plan_id: int,
    context: dict = Depends(get_template_context),
    current_camp: models.Camp = Depends(get_current_camp),
    db: Session = Depends(get_db),
):
    if not current_camp:
        raise HTTPException(status_code=400, detail="Kein Camp ausgewaehlt")

    meal_plan = crud.get_meal_plan(db, meal_plan_id)
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Mahlzeit nicht gefunden")

    existing_entries = crud.get_leftovers_for_meal_plan(db, meal_plan_id)
    recipe = meal_plan.recipe
    context.update(
        {
            "meal_plan": meal_plan,
            "recipe": recipe,
            "ingredients": recipe.ingredients if recipe else [],
            "camp": current_camp,
            "existing_entries": existing_entries,
        }
    )
    return templates.TemplateResponse("leftovers/new_modal.html", context)


@router.get("/api/by-meal-plan/{meal_plan_id}", response_model=list[schemas.Leftover])
async def get_leftovers_by_meal_plan(meal_plan_id: int, db: Session = Depends(get_db)):
    """Story 7: a meal plan can have multiple leftover entries (per_recipe + N per_ingredient)."""
    return crud.get_leftovers_for_meal_plan(db, meal_plan_id)


@router.post("/api/meal-plan/{meal_plan_id}/sync", response_model=list[schemas.Leftover])
async def sync_meal_plan_leftovers(
    meal_plan_id: int,
    payload: schemas.LeftoverSyncRequest,
    current_camp: models.Camp = Depends(get_current_camp),
    db: Session = Depends(get_db),
):
    """Replace all leftover entries for a meal plan with the given list (Story 7)."""
    if not current_camp:
        raise HTTPException(status_code=400, detail="Kein Camp ausgewaehlt")

    meal_plan = crud.get_meal_plan(db, meal_plan_id)
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Mahlzeit nicht gefunden")
    if meal_plan.camp_id != current_camp.id:
        raise HTTPException(status_code=403, detail="Mahlzeit gehoert nicht zum aktuellen Camp")

    entries_data = [entry.model_dump() for entry in payload.entries]
    created = crud.sync_leftovers_for_meal_plan(
        db,
        camp_id=current_camp.id,
        meal_plan_id=meal_plan_id,
        recipe_id=meal_plan.recipe_id,
        entries=entries_data,
    )
    logger.info(f"Leftovers sync: meal_plan={meal_plan_id} camp={current_camp.id} created={len(created)} (replaced)")
    return created


@router.put("/api/leftovers/{leftover_id}", response_model=schemas.Leftover)
async def update_leftover(
    leftover_id: int,
    update: schemas.LeftoverUpdate,
    db: Session = Depends(get_db),
):
    updated = crud.update_leftover(db, leftover_id, update.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")
    logger.info(f"Leftover updated: id={updated.id}")
    return updated


@router.post("/api/leftovers", response_model=schemas.Leftover)
async def create_leftover(
    leftover: schemas.LeftoverCreate,
    db: Session = Depends(get_db),
):
    if not crud.get_camp(db, leftover.camp_id):
        raise HTTPException(status_code=404, detail="Camp nicht gefunden")
    saved = crud.create_leftover(db, leftover)
    logger.info(f"Leftover created: id={saved.id} camp={saved.camp_id} recipe={saved.recipe_id}")
    return saved


@router.get("/api/leftovers/camp/{camp_id}")
async def list_camp_leftovers(camp_id: int, db: Session = Depends(get_db)):
    return crud.get_leftovers_for_camp(db, camp_id)


@router.get("/api/leftovers/statistics/{recipe_id}", response_model=schemas.LeftoverStatistics)
async def recipe_statistics(
    recipe_id: int,
    current_camp: models.Camp = Depends(get_current_camp),
    db: Session = Depends(get_db),
):
    camp_id = current_camp.id if current_camp else None
    return get_recipe_statistics(db, recipe_id, current_camp_id=camp_id)


@router.delete("/api/leftovers/{leftover_id}")
async def delete_leftover(leftover_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_leftover(db, leftover_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")
    return ""


@router.get("/statistics", response_class=HTMLResponse)
async def statistics_page(
    request: Request,
    context: dict = Depends(get_template_context),
    current_camp: models.Camp = Depends(get_current_camp),
    db: Session = Depends(get_db),
):
    if not current_camp:
        return templates.TemplateResponse("meal_planning/no_camp.html", context)

    # Aggregate per recipe across all leftovers we have data for.
    recipe_ids = {lo.recipe_id for lo in db.query(models.Leftover).filter(models.Leftover.recipe_id.isnot(None)).all()}
    stats = []
    for rid in recipe_ids:
        s = get_recipe_statistics(db, rid, current_camp_id=current_camp.id)
        breakdown = get_ingredient_breakdown(db, rid)
        # Enrich per-recipe stats so the template can distinguish per_recipe
        # vs per_ingredient sources (Story 8 follow-up).
        s["ingredient_breakdown"] = breakdown
        s["has_per_recipe"] = s["total_entries"] > 0
        s["has_per_ingredient"] = len(breakdown) > 0
        stats.append(s)
    # Sort: per-recipe avg first (descending), then per-ingredient-only recipes.
    stats.sort(key=lambda s: s["avg_percentage_left"] or 0, reverse=True)

    context.update({"camp": current_camp, "stats": stats})
    return templates.TemplateResponse("leftovers/statistics.html", context)
