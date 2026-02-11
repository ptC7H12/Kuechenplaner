from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.dependencies import get_current_camp, get_template_context, templates
from app import crud, schemas, models
from app.logging_config import get_logger

logger = get_logger("meal_planning")

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def meal_planning_page(
    request: Request,
    context: dict = Depends(get_template_context),
    current_camp: models.Camp = Depends(get_current_camp),
    db: Session = Depends(get_db)
):
    """Meal planning page with calendar grid"""
    if not current_camp:
        return templates.TemplateResponse("meal_planning/no_camp.html", context)

    meal_plans = crud.get_meal_plans_for_camp(db, current_camp.id)
    recipes = crud.get_recipes(db, skip=0, limit=1000)

    # Generate date range for the camp
    days = []
    current_date = current_camp.start_date
    while current_date <= current_camp.end_date:
        days.append(current_date)
        current_date += timedelta(days=1)

    # Organize meal plans by date and meal type
    meal_grid = {}
    for day in days:
        meal_grid[day.date()] = {
            models.MealType.BREAKFAST: [],
            models.MealType.LUNCH: [],
            models.MealType.DINNER: []
        }

    for meal_plan in meal_plans:
        date_key = meal_plan.meal_date.date()
        if date_key in meal_grid:
            meal_grid[date_key][meal_plan.meal_type].append(meal_plan)

    context.update({
        "camp": current_camp,
        "days": days,
        "meal_grid": meal_grid,
        "recipes": recipes,
        "meal_types": [models.MealType.BREAKFAST, models.MealType.LUNCH, models.MealType.DINNER]
    })

    return templates.TemplateResponse("meal_planning/index.html", context)

@router.get("/api/meal-plans")
async def get_meal_plans(
    camp_id: int,
    db: Session = Depends(get_db)
):
    """Get all meal plans for a camp (API endpoint)"""
    camp = crud.get_camp(db, camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    return crud.get_meal_plans_for_camp(db, camp_id)

@router.post("/api/meal-plans", response_model=schemas.MealPlan)
async def create_meal_plan(
    meal_plan: schemas.MealPlanCreate,
    db: Session = Depends(get_db)
):
    """Create a new meal plan (API endpoint)"""
    camp = crud.get_camp(db, meal_plan.camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    if meal_plan.recipe_id is not None:
        recipe = crud.get_recipe(db, meal_plan.recipe_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

    return crud.create_meal_plan(db, meal_plan)

@router.put("/api/meal-plans/{meal_plan_id}", response_model=schemas.MealPlan)
async def update_meal_plan(
    meal_plan_id: int,
    meal_plan_update: schemas.MealPlanUpdate,
    db: Session = Depends(get_db)
):
    """Update a meal plan (API endpoint)"""
    meal_plan = crud.update_meal_plan(db, meal_plan_id, meal_plan_update)
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    return meal_plan

@router.delete("/api/meal-plans/{meal_plan_id}")
async def delete_meal_plan(
    meal_plan_id: int,
    db: Session = Depends(get_db)
):
    """Delete a meal plan (API endpoint)"""
    meal_plan = crud.delete_meal_plan(db, meal_plan_id)
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    return ""

@router.post("/api/meal-plans/bulk")
async def create_bulk_meal_plans(
    meal_plans: List[schemas.MealPlanCreate],
    db: Session = Depends(get_db)
):
    """Create multiple meal plans at once (bulk operation)"""
    created_plans = []
    for meal_plan_data in meal_plans:
        meal_plan = crud.create_meal_plan(db, meal_plan_data)
        created_plans.append(meal_plan)

    return {
        "success": True,
        "count": len(created_plans),
        "meal_plans": created_plans
    }

@router.post("/api/meal-plans/{meal_plan_id}/copy")
async def copy_meal_plan(
    meal_plan_id: int,
    target_date: datetime,
    target_meal_type: Optional[models.MealType] = None,
    db: Session = Depends(get_db)
):
    """Copy a meal plan to another date/meal type"""
    original = crud.get_meal_plan(db, meal_plan_id)
    if not original:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    new_meal_plan = schemas.MealPlanCreate(
        camp_id=original.camp_id,
        recipe_id=original.recipe_id,
        meal_date=target_date,
        meal_type=target_meal_type or original.meal_type,
        position=0,
        notes=original.notes
    )

    return crud.create_meal_plan(db, new_meal_plan)
