from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_camp, get_template_context, templates
from app.services.calculation import calculate_shopping_list

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def shopping_list_page(
    request: Request,
    context: dict = Depends(get_template_context),
    current_camp: models.Camp = Depends(get_current_camp),
    db: Session = Depends(get_db),
):
    """Shopping list page"""
    if not current_camp:
        return templates.TemplateResponse("shopping_list/no_camp.html", context)

    shopping_data = calculate_shopping_list(db, current_camp.id)

    context.update(
        {
            "camp": shopping_data["camp"],
            "categories": shopping_data["categories"],
            "category_colors": shopping_data["category_colors"],
            "total_items": shopping_data["total_items"],
            "total_recipes": shopping_data["total_recipes"],
        }
    )

    return templates.TemplateResponse("shopping_list.html", context)


@router.get("/api/shopping-list")
async def get_shopping_list(camp_id: int, db: Session = Depends(get_db)):
    """Get shopping list for a camp (API endpoint)"""
    camp = crud.get_camp(db, camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    return calculate_shopping_list(db, camp_id)


@router.get("/api/shopping-list/summary")
async def get_shopping_list_summary(camp_id: int, db: Session = Depends(get_db)):
    """Get shopping list summary with statistics"""
    camp = crud.get_camp(db, camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    shopping_data = calculate_shopping_list(db, camp_id)

    return {
        "camp_id": camp_id,
        "camp_name": camp.name,
        "participant_count": camp.participant_count,
        "total_items": shopping_data["total_items"],
        "total_categories": len(shopping_data["categories"]),
        "total_recipes": shopping_data["total_recipes"],
        "categories": list(shopping_data["categories"].keys()),
    }


@router.put("/api/shopping-list/notes/{ingredient_id}")
async def upsert_shopping_list_note(
    ingredient_id: int,
    payload: schemas.ShoppingListNoteUpdate,
    current_camp: models.Camp = Depends(get_current_camp),
    db: Session = Depends(get_db),
):
    """Create, update or delete (empty note) a camp-specific note for a shopping list item."""
    if not current_camp:
        raise HTTPException(status_code=400, detail="Kein Camp ausgewaehlt")

    ingredient = crud.get_ingredient(db, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Zutat nicht gefunden")

    saved = crud.upsert_shopping_list_note(db, current_camp.id, ingredient_id, payload.note)
    return {
        "ingredient_id": ingredient_id,
        "note": saved.note if saved else None,
    }


@router.put("/api/ingredients/{ingredient_id}/note")
async def update_ingredient_global_note(
    ingredient_id: int,
    payload: schemas.ShoppingListNoteUpdate,
    db: Session = Depends(get_db),
):
    """Update the global note on an ingredient (applies to all camps)."""
    updated = crud.update_ingredient_note(db, ingredient_id, payload.note)
    if not updated:
        raise HTTPException(status_code=404, detail="Zutat nicht gefunden")
    return {"ingredient_id": ingredient_id, "note": updated.note}
