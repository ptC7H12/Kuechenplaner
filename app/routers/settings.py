from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
import tempfile
import os

from app.database import get_db
from app.dependencies import get_current_camp, get_template_context, templates
from app import crud, schemas, models
from app.logging_config import get_logger

logger = get_logger("settings")

router = APIRouter()


def safe_json_load(value: str) -> Any:
    """Safely parse JSON or return string value"""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError, ValueError):
        return value

@router.get("/", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    context: dict = Depends(get_template_context),
    current_camp: models.Camp = Depends(get_current_camp),
    db: Session = Depends(get_db)
):
    """Settings page"""
    all_settings = db.query(models.AppSettings).all()
    settings_dict = {setting.key: safe_json_load(setting.value) for setting in all_settings}

    tags = crud.get_tags(db)
    allergens = crud.get_allergens(db)
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
    return crud.get_setting_value(db, "unit_conversions", default={})

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
    form_data = await request.form()
    name = form_data.get("name")
    icon = form_data.get("icon", "🏷️")
    color = form_data.get("color", "#3B82F6")

    if not name:
        raise HTTPException(status_code=400, detail="Tag name is required")

    existing_tag = db.query(models.Tag).filter(models.Tag.name == name).first()
    if existing_tag:
        raise HTTPException(status_code=400, detail="Tag already exists")

    tag = models.Tag(name=name, icon=icon, color=color)
    db.add(tag)
    db.commit()
    db.refresh(tag)

    html = f"""
    <div class="flex items-center justify-between p-4 border-2 border-gray-200 rounded-xl bg-white hover:shadow-lg transition-all" id="tag-{tag.id}">
        <div class="flex items-center space-x-3">
            <span class="text-2xl">{tag.icon or '🏷️'}</span>
            <span class="font-semibold text-gray-900">{tag.name}</span>
            <div class="w-5 h-5 rounded-full border-2 border-gray-200 shadow-sm" style="background-color: {tag.color}"></div>
        </div>
        <button hx-delete="/settings/api/tags/{tag.id}"
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

    logger.info(f"Tag deleted: {tag.name} (ID: {tag_id})")
    db.delete(tag)
    db.commit()

    return HTMLResponse(content="", status_code=200)


# Excel Recipe Import
def _guess_ingredient_category(ingredient_name: str) -> str:
    """Guess ingredient category based on name"""
    ingredient_lower = ingredient_name.lower()

    categories = {
        "Gemüse": ['kartoffel', 'zwiebel', 'knoblauch', 'tomat', 'gurke', 'paprika',
                    'möhre', 'karotte', 'sellerie', 'lauch', 'zucchini', 'aubergine',
                    'brokkoli', 'blumenkohl', 'kohl', 'salat', 'spinat', 'erbsen'],
        "Obst": ['apfel', 'birne', 'banane', 'orange', 'zitrone', 'beeren',
                  'erdbeere', 'himbeere', 'kirsche', 'pflaume', 'pfirsich'],
        "Fleisch": ['fleisch', 'hack', 'rind', 'schwein', 'hähnchen', 'huhn',
                     'pute', 'schnitzel', 'würstchen', 'wurst', 'speck', 'schinken'],
        "Fisch": ['fisch', 'lachs', 'thunfisch', 'forelle', 'garnele', 'krabbe'],
        "Milchprodukte": ['milch', 'sahne', 'butter', 'käse', 'quark', 'joghurt',
                           'schmand', 'creme', 'frischkäse'],
        "Getreide": ['mehl', 'reis', 'nudel', 'pasta', 'brot', 'brötchen',
                      'haferflocken', 'müsli', 'couscous', 'bulgur'],
        "Backwaren": ['zucker', 'backpulver', 'hefe', 'vanille', 'kakao'],
        "Öle & Fette": ['öl', 'olivenöl', 'sonnenblumenöl', 'margarine', 'fett'],
        "Gewürze": ['salz', 'pfeffer', 'paprika', 'curry', 'zimt', 'muskat',
                     'kräuter', 'petersilie', 'basilikum', 'oregano', 'thymian',
                     'rosmarin', 'majoran', 'kümmel', 'koriander'],
        "Konserven": ['dose', 'konserve', 'passiert', 'geschält', 'tomatenmark'],
    }

    for category, keywords in categories.items():
        if any(kw in ingredient_lower for kw in keywords):
            return category

    if 'ei' in ingredient_lower or 'eier' in ingredient_lower:
        return "Milchprodukte"

    return "Sonstiges"


def _import_recipe_from_sheet(db: Session, sheet):
    """Import a single recipe from an Excel sheet"""
    recipe_name = sheet['A1'].value
    if not recipe_name:
        return None, f"Blatt '{sheet.title}': Kein Rezeptname in A1"

    recipe_name = str(recipe_name).strip()

    # Check for duplicate
    existing = db.query(models.Recipe).filter(models.Recipe.name == recipe_name).first()
    if existing:
        return None, f"'{recipe_name}': Existiert bereits"

    base_servings = sheet['A4'].value
    if not base_servings or not isinstance(base_servings, (int, float)):
        base_servings = 30
    else:
        base_servings = int(base_servings)

    ingredients = []
    for row in range(5, 31):
        quantity_cell = sheet[f'A{row}'].value
        unit_cell = sheet[f'C{row}'].value
        ingredient_cell = sheet[f'D{row}'].value

        if not ingredient_cell:
            break
        if not quantity_cell:
            continue

        try:
            if isinstance(quantity_cell, str):
                quantity_cell = quantity_cell.replace(',', '.')
            quantity = float(quantity_cell)
        except (ValueError, TypeError):
            continue

        unit = str(unit_cell).strip() if unit_cell else "Stück"
        ingredient_name = str(ingredient_cell).strip()
        category = _guess_ingredient_category(ingredient_name)

        db_ingredient = crud.get_or_create_ingredient(db, name=ingredient_name, unit=unit, category=category)
        ingredients.append({
            'ingredient_id': db_ingredient.id,
            'quantity': quantity,
            'unit': unit
        })

    instructions_lines = []
    for row in range(31, sheet.max_row + 1):
        cell_value = sheet[f'A{row}'].value
        if cell_value:
            instructions_lines.append(str(cell_value).strip())

    instructions = "\n".join(instructions_lines) if instructions_lines else None

    recipe_data = schemas.RecipeCreate(
        name=recipe_name,
        base_servings=base_servings,
        instructions=instructions,
        ingredients=[schemas.RecipeIngredientCreate(**ing) for ing in ingredients],
        tag_ids=[],
        allergen_ids=[]
    )

    db_recipe = crud.create_recipe(db, recipe_data)
    return db_recipe, None


@router.post("/api/import-recipes")
async def import_recipes_from_excel(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Import recipes from an Excel file"""
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        return HTMLResponse(
            content='<div class="alert alert-error">Bitte eine Excel-Datei (.xlsx) hochladen.</div>',
            status_code=400
        )

    try:
        from openpyxl import load_workbook

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            workbook = load_workbook(tmp_path, data_only=True)
        finally:
            os.unlink(tmp_path)

        imported = []
        skipped = []

        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            try:
                recipe, error = _import_recipe_from_sheet(db, sheet)
                if recipe:
                    imported.append(recipe.name)
                elif error:
                    skipped.append(error)
            except Exception as e:
                skipped.append(f"'{sheet_name}': {str(e)}")

        logger.info(f"Excel import: {len(imported)} imported, {len(skipped)} skipped")

        # Build result HTML
        result_parts = []
        if imported:
            recipes_list = "".join(f"<li>{name}</li>" for name in imported)
            result_parts.append(
                f'<div class="alert alert-success mb-3">'
                f'<strong>{len(imported)} Rezept(e) erfolgreich importiert:</strong>'
                f'<ul class="list-disc ml-6 mt-2">{recipes_list}</ul></div>'
            )
        if skipped:
            skip_list = "".join(f"<li>{msg}</li>" for msg in skipped)
            result_parts.append(
                f'<div class="alert alert-warning">'
                f'<strong>{len(skipped)} übersprungen:</strong>'
                f'<ul class="list-disc ml-6 mt-2">{skip_list}</ul></div>'
            )
        if not imported and not skipped:
            result_parts.append(
                '<div class="alert alert-warning">Keine Rezepte in der Datei gefunden.</div>'
            )

        return HTMLResponse(content="".join(result_parts))

    except Exception as e:
        logger.error(f"Excel import error: {e}", exc_info=True)
        return HTMLResponse(
            content=f'<div class="alert alert-error">Fehler beim Import: {str(e)}</div>',
            status_code=500
        )
