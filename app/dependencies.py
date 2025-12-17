from fastapi import Depends, HTTPException, Request, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app import crud, models

def get_current_camp(
    request: Request,
    current_camp_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[models.Camp]:
    """Get the currently selected camp from cookie or session"""
    
    camp_id = None
    
    # Try to get from cookie first
    if current_camp_id:
        try:
            camp_id = int(current_camp_id)
        except (ValueError, TypeError):
            pass
    
    # If no cookie, try to get last selected from settings
    if not camp_id:
        last_selected = crud.get_setting_value(db, "last_selected_camp_id")
        if last_selected:
            try:
                camp_id = int(last_selected)
            except (ValueError, TypeError):
                pass
    
    # Get the camp from database
    if camp_id:
        camp = crud.get_camp(db, camp_id)
        if camp:
            # Update last accessed time
            crud.update_camp_last_accessed(db, camp_id)
            return camp
    
    return None

def require_current_camp(
    current_camp: Optional[models.Camp] = Depends(get_current_camp)
) -> models.Camp:
    """Require a current camp to be selected"""
    if not current_camp:
        raise HTTPException(status_code=400, detail="No camp selected")
    return current_camp

def get_template_context(
    request: Request,
    current_camp: Optional[models.Camp] = Depends(get_current_camp),
    db: Session = Depends(get_db)
) -> dict:
    """Get common template context"""
    return {
        "request": request,
        "current_camp": current_camp,
        "db": db,
        "timedelta": timedelta,
        "datetime": datetime
    }