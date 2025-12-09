from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json

from app.database import get_db
from app.dependencies import get_current_camp, get_template_context
from app import crud, schemas, models

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    context: dict = Depends(get_template_context),
    current_camp: models.Camp = Depends(get_current_camp),
    db: Session = Depends(get_db)
):
    """Settings page"""

    # Get all settings
    all_settings = db.query(models.AppSettings).all()
    settings_dict = {setting.key: json.loads(setting.value) if setting.value.startswith('{') or setting.value.startswith('[') else setting.value for setting in all_settings}

    # Get all tags and allergens
    tags = crud.get_tags(db)
    allergens = crud.get_allergens(db)

    # Get all camps for management
    camps = crud.get_camps(db)

    context.update({
        "settings": settings_dict,
        "tags": tags,
        "allergens": allergens,
        "camps": camps,
        "current_camp": current_camp
    })

    return templates.TemplateResponse("settings/index.html", context)

@router.get("/api/settings")
async def get_all_settings(db: Session = Depends(get_db)):
    """Get all settings (API endpoint)"""

    settings = db.query(models.AppSettings).all()
    return {
        setting.key: crud.get_setting_value(db, setting.key)
        for setting in settings
    }

@router.get("/api/settings/{key}")
async def get_setting(
    key: str,
    db: Session = Depends(get_db)
):
    """Get a specific setting (API endpoint)"""

    value = crud.get_setting_value(db, key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    return {"key": key, "value": value}

@router.post("/api/settings")
async def update_setting(
    key: str,
    value: Any,
    db: Session = Depends(get_db)
):
    """Update or create a setting (API endpoint)"""

    crud.set_setting_value(db, key, value)
    return {"success": True, "key": key, "value": value}

@router.put("/api/settings/{key}")
async def update_specific_setting(
    key: str,
    value: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update a specific setting (API endpoint)"""

    crud.set_setting_value(db, key, value.get("value"))
    return {"success": True, "key": key, "value": value.get("value")}

@router.delete("/api/settings/{key}")
async def delete_setting(
    key: str,
    db: Session = Depends(get_db)
):
    """Delete a setting (API endpoint)"""

    setting = crud.get_setting(db, key)
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    db.delete(setting)
    db.commit()

    return {"success": True, "message": f"Setting '{key}' deleted"}

# Unit conversion settings
@router.get("/api/settings/units/conversions")
async def get_unit_conversions(db: Session = Depends(get_db)):
    """Get unit conversion settings"""

    conversions = crud.get_setting_value(db, "unit_conversions", default={})
    return conversions

@router.post("/api/settings/units/conversions")
async def update_unit_conversions(
    conversions: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update unit conversion settings"""

    crud.set_setting_value(db, "unit_conversions", conversions)
    return {"success": True, "conversions": conversions}
