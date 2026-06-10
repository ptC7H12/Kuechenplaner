import contextlib
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Cookie, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import crud, models
from app.database import get_db

# Centralized templates instance - import this in routers
_BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=_BASE_DIR / "templates")


def get_current_camp(
    request: Request, current_camp_id: str | None = Cookie(None), db: Session = Depends(get_db)
) -> models.Camp | None:
    """Get the currently selected camp from cookie or session"""

    camp_id = None

    # Try to get from cookie first
    if current_camp_id:
        with contextlib.suppress(ValueError, TypeError):
            camp_id = int(current_camp_id)

    # If no cookie, try to get last selected from settings
    if not camp_id:
        last_selected = crud.get_setting_value(db, "last_selected_camp_id")
        if last_selected:
            with contextlib.suppress(ValueError, TypeError):
                camp_id = int(last_selected)

    # Get the camp from database
    if camp_id:
        camp = crud.get_camp(db, camp_id)
        if camp:
            # Update last accessed time
            crud.update_camp_last_accessed(db, camp_id)
            return camp

    return None


def require_current_camp(current_camp: models.Camp | None = Depends(get_current_camp)) -> models.Camp:
    """Require a current camp to be selected"""
    if not current_camp:
        raise HTTPException(status_code=400, detail="No camp selected")
    return current_camp


def get_template_context(
    request: Request,
    current_camp: models.Camp | None = Depends(get_current_camp),
) -> dict:
    """Get common template context"""
    return {"request": request, "current_camp": current_camp, "timedelta": timedelta, "datetime": datetime}
