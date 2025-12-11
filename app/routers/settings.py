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

# Tag management endpoints
@router.post("/api/tags")
async def create_tag(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new tag"""
    from fastapi.responses import HTMLResponse

    form_data = await request.form()
    name = form_data.get("name")
    icon = form_data.get("icon", "🏷️")
    color = form_data.get("color", "#3B82F6")

    if not name:
        raise HTTPException(status_code=400, detail="Tag name is required")

    # Check if tag already exists
    existing_tag = db.query(models.Tag).filter(models.Tag.name == name).first()
    if existing_tag:
        raise HTTPException(status_code=400, detail="Tag already exists")

    # Create tag
    tag = models.Tag(name=name, icon=icon, color=color)
    db.add(tag)
    db.commit()
    db.refresh(tag)

    # Return HTML for the new tag card
    html = f"""
    <div class="flex items-center justify-between p-4 border-2 border-gray-200 rounded-xl bg-white hover:shadow-lg transition-all" id="tag-{tag.id}">
        <div class="flex items-center space-x-3">
            <span class="text-2xl">{tag.icon or '🏷️'}</span>
            <span class="font-semibold text-gray-900">{tag.name}</span>
            <div class="w-5 h-5 rounded-full border-2 border-gray-200 shadow-sm" style="background-color: {tag.color}"></div>
        </div>
        <button hx-delete="/api/tags/{tag.id}"
                hx-confirm="Tag '{tag.name}' wirklich löschen?"
                hx-target="#tag-{tag.id}"
                hx-swap="outerHTML swap:0.3s"
                class="text-red-600 hover:text-red-800 hover:bg-red-50 p-2 rounded-lg transition-all">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
        </button>
    </div>
    """

    return HTMLResponse(content=html, status_code=201)

@router.delete("/api/tags/{tag_id}")
async def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db)
):
    """Delete a tag"""

    tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    db.delete(tag)
    db.commit()

    return {"success": True, "message": f"Tag '{tag.name}' deleted"}
