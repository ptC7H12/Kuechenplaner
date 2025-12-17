from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Optional
import logging

from app.database import get_db
from app.dependencies import get_current_camp, get_template_context
from app import crud, schemas
from app.services.calculation import get_camp_statistics

logger = logging.getLogger("kuechenplaner.camps")

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

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
    try:
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Validate dates
        if end_dt <= start_dt:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        # Create camp
        camp_data = schemas.CampCreate(
            name=name,
            start_date=start_dt,
            end_date=end_dt,
            participant_count=participant_count
        )
        
        camp = crud.create_camp(db, camp_data)

        logger.info(f"Camp created: {camp.name} (ID: {camp.id})")

        # Set as current camp
        crud.set_setting_value(db, "last_selected_camp_id", camp.id)

        # Redirect to dashboard with cookie
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(key="current_camp_id", value=str(camp.id))
        return response

    except ValueError as e:
        logger.warning(f"Invalid date format in camp creation: {e}")
        raise HTTPException(status_code=400, detail="Ungültiges Datumsformat")
    except SQLAlchemyError as e:
        logger.error(f"Database error creating camp: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Datenbankfehler beim Erstellen der Freizeit")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating camp: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unerwarteter Fehler")

@router.post("/{camp_id}/select", response_class=RedirectResponse)
async def select_camp(
    camp_id: int,
    db: Session = Depends(get_db)
):
    """Select a camp as current"""
    camp = crud.get_camp(db, camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")
    
    # Update last accessed and set as current
    crud.update_camp_last_accessed(db, camp_id)
    crud.set_setting_value(db, "last_selected_camp_id", camp_id)
    
    # Redirect to dashboard with cookie
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
    
    # If this was the current camp, clear the setting
    current_camp_id = crud.get_setting_value(db, "last_selected_camp_id")
    if current_camp_id == camp_id:
        crud.set_setting_value(db, "last_selected_camp_id", None)
    
    # Return empty response (HTMX will remove the element)
    return ""

@router.get("/{camp_id}/stats", response_class=HTMLResponse)
async def get_camp_stats(
    camp_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get camp statistics (for HTMX updates)"""
    stats = get_camp_statistics(db, camp_id)
    
    # Return just the stats part as HTML fragment
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
    try:
        update_data = {}
        
        if name is not None:
            update_data["name"] = name
        if participant_count is not None:
            update_data["participant_count"] = participant_count
        if start_date is not None:
            update_data["start_date"] = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date is not None:
            update_data["end_date"] = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Validate dates if both are provided
        if "start_date" in update_data and "end_date" in update_data:
            if update_data["end_date"] <= update_data["start_date"]:
                raise HTTPException(status_code=400, detail="End date must be after start date")
        
        camp_update = schemas.CampUpdate(**update_data)
        camp = crud.update_camp(db, camp_id, camp_update)

        if not camp:
            raise HTTPException(status_code=404, detail="Camp not found")

        logger.info(f"Camp updated: {camp.name} (ID: {camp_id})")

        # Return success response (HTMX will close modal and refresh page)
        return '<script>window.location.reload();</script>'

    except ValueError as e:
        logger.warning(f"Invalid date format in camp update: {e}")
        raise HTTPException(status_code=400, detail="Ungültiges Datumsformat")
    except SQLAlchemyError as e:
        logger.error(f"Database error updating camp {camp_id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Datenbankfehler beim Aktualisieren der Freizeit")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating camp {camp_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unerwarteter Fehler")