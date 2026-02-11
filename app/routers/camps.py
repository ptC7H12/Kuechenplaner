from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_camp, get_template_context, templates
from app import crud, schemas
from app.services.calculation import get_camp_statistics
from app.logging_config import get_logger

logger = get_logger("camps")

router = APIRouter()

@router.get("/create", response_class=HTMLResponse)
async def create_camp_form(
    request: Request,
    context: dict = Depends(get_template_context)
):
    """Show create camp form"""
    return templates.TemplateResponse("camp_create.html", context)

@router.post("/", response_class=RedirectResponse)
async def create_camp(
    name: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    participant_count: int = Form(...),
    db: Session = Depends(get_db)
):
    """Create a new camp"""
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    camp_data = schemas.CampCreate(
        name=name,
        start_date=start_dt,
        end_date=end_dt,
        participant_count=participant_count
    )

    camp = crud.create_camp(db, camp_data)
    logger.info(f"Camp created: {camp.name} (ID: {camp.id})")

    crud.set_setting_value(db, "last_selected_camp_id", camp.id)

    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="current_camp_id", value=str(camp.id))
    return response

@router.post("/{camp_id}/select", response_class=RedirectResponse)
async def select_camp(
    camp_id: int,
    db: Session = Depends(get_db)
):
    """Select a camp as current"""
    camp = crud.get_camp(db, camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    crud.update_camp_last_accessed(db, camp_id)
    crud.set_setting_value(db, "last_selected_camp_id", camp_id)

    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="current_camp_id", value=str(camp_id))
    return response

@router.delete("/{camp_id}", response_class=HTMLResponse)
async def delete_camp(
    camp_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a camp"""
    camp = crud.delete_camp(db, camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    current_camp_id = crud.get_setting_value(db, "last_selected_camp_id")
    if current_camp_id == camp_id:
        crud.set_setting_value(db, "last_selected_camp_id", None)

    return ""

@router.get("/{camp_id}/stats", response_class=HTMLResponse)
async def get_camp_stats(
    camp_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get camp statistics (for HTMX updates)"""
    stats = get_camp_statistics(db, camp_id)

    return templates.TemplateResponse("components/camp_stats.html", {
        "request": request,
        "stats": stats
    })

@router.get("/{camp_id}/edit", response_class=HTMLResponse)
async def edit_camp_modal(
    camp_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Show edit camp modal"""
    camp = crud.get_camp(db, camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    return templates.TemplateResponse("components/edit_camp_modal.html", {
        "request": request,
        "camp": camp
    })

@router.put("/{camp_id}", response_class=HTMLResponse)
async def update_camp(
    camp_id: int,
    request: Request,
    name: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    participant_count: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """Update a camp"""
    update_data = {}

    if name is not None:
        update_data["name"] = name
    if participant_count is not None:
        update_data["participant_count"] = participant_count
    if start_date is not None:
        update_data["start_date"] = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date is not None:
        update_data["end_date"] = datetime.strptime(end_date, "%Y-%m-%d")

    camp_update = schemas.CampUpdate(**update_data)
    camp = crud.update_camp(db, camp_id, camp_update)

    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    logger.info(f"Camp updated: {camp.name} (ID: {camp_id})")

    return '<script>window.location.reload();</script>'
