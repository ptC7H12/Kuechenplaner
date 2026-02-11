from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.database import get_db
from app.dependencies import get_current_camp, get_template_context, templates
from app import crud, schemas, models
from app.logging_config import get_logger

logger = get_logger("recipes")

router = APIRouter()


def parse_recipe_form_data(ingredients: str, tag_ids: str):
    """Parse JSON form data for recipe creation/update"""
    try:
        ingredients_list = json.loads(ingredients)
        tag_ids_list = json.loads(tag_ids)

        ingredient_objects = [
            schemas.RecipeIngredientCreate(**ing) for ing in ingredients_list
        ]

        return ingredient_objects, tag_ids_list

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Ungültige JSON-Daten: {str(e)}")
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Ungültige Zutatendaten: {str(e)}")

@router.get("/", response_class=HTMLResponse)
async def list_recipes(
    request: Request,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    context: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    """List all recipes with optional filtering"""
    recipes = crud.get_recipes(db, skip=0, limit=100)
    all_tags = crud.get_tags(db)
    all_allergens = crud.get_allergens(db)

    context.update({
        "recipes": recipes,
        "tags": all_tags,
        "allergens": all_allergens,
        "search": search or "",
        "selected_tags": tags.split(",") if tags else []
    })

    return templates.TemplateResponse("recipes/list.html", context)

@router.get("/create", response_class=HTMLResponse)
async def create_recipe_form(
    request: Request,
    context: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    """Show create recipe form"""
    ingredients = crud.get_ingredients(db)
    tags = crud.get_tags(db)

    context.update({
        "ingredients": ingredients,
        "tags": tags
    })

    return templates.TemplateResponse("recipes/create.html", context)

@router.post("/", response_class=HTMLResponse)
async def create_recipe(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    base_servings: int = Form(...),
    instructions: str = Form(...),
    preparation_time: Optional[int] = Form(None),
    cooking_time: Optional[int] = Form(None),
    allergen_notes: Optional[str] = Form(None),
    ingredients: str = Form(...),  # JSON string
    tag_ids: str = Form("[]"),  # JSON string
    db: Session = Depends(get_db)
):
    """Create a new recipe"""
    ingredient_objects, tag_ids_list = parse_recipe_form_data(ingredients, tag_ids)

    recipe_data = schemas.RecipeCreate(
        name=name,
        description=description,
        base_servings=base_servings,
        instructions=instructions,
        preparation_time=preparation_time,
        cooking_time=cooking_time,
        allergen_notes=allergen_notes,
        ingredients=ingredient_objects,
        tag_ids=tag_ids_list
    )

    recipe = crud.create_recipe(db, recipe_data)
    logger.info(f"Recipe created: {recipe.name} (ID: {recipe.id})")

    return RedirectResponse(url=f"/recipes/{recipe.id}", status_code=303)

@router.get("/{recipe_id}", response_class=HTMLResponse)
async def get_recipe(
    recipe_id: int,
    request: Request,
    context: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    """Get recipe details"""
    recipe = crud.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    context.update({"recipe": recipe})
    return templates.TemplateResponse("recipes/detail.html", context)

@router.get("/{recipe_id}/edit", response_class=HTMLResponse)
async def edit_recipe_form(
    recipe_id: int,
    request: Request,
    context: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    """Show edit recipe form"""
    recipe = crud.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    tags = crud.get_tags(db)

    context.update({
        "recipe": recipe,
        "tags": tags
    })

    return templates.TemplateResponse("recipes/edit.html", context)

@router.put("/{recipe_id}", response_class=HTMLResponse)
async def update_recipe(
    recipe_id: int,
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    base_servings: int = Form(...),
    instructions: str = Form(...),
    preparation_time: Optional[int] = Form(None),
    cooking_time: Optional[int] = Form(None),
    allergen_notes: Optional[str] = Form(None),
    ingredients: str = Form(...),  # JSON string
    tag_ids: str = Form("[]"),  # JSON string
    db: Session = Depends(get_db)
):
    """Update an existing recipe"""
    existing_recipe = crud.get_recipe(db, recipe_id)
    if not existing_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    ingredient_objects, tag_ids_list = parse_recipe_form_data(ingredients, tag_ids)

    recipe_update = schemas.RecipeUpdate(
        name=name,
        description=description,
        base_servings=base_servings,
        instructions=instructions,
        preparation_time=preparation_time,
        cooking_time=cooking_time,
        allergen_notes=allergen_notes,
        ingredients=ingredient_objects,
        tag_ids=tag_ids_list
    )

    updated_recipe = crud.update_recipe(db, recipe_id, recipe_update)
    logger.info(f"Recipe updated: {updated_recipe.name} (ID: {recipe_id})")

    return RedirectResponse(url=f"/recipes/{recipe_id}", status_code=303)

@router.get("/{recipe_id}/versions", response_class=HTMLResponse)
async def get_recipe_versions(
    recipe_id: int,
    request: Request,
    context: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    """Get all versions of a recipe"""
    recipe = crud.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    versions = crud.get_recipe_versions(db, recipe_id)

    for version in versions:
        version.ingredients_parsed = json.loads(version.ingredients_snapshot) if version.ingredients_snapshot else []
        version.tags_parsed = json.loads(version.tags_snapshot) if version.tags_snapshot else []
        version.allergens_parsed = json.loads(version.allergens_snapshot) if version.allergens_snapshot else []

    context.update({
        "recipe": recipe,
        "versions": versions,
        "current_version": recipe.version_number
    })

    return templates.TemplateResponse("recipes/versions.html", context)

@router.delete("/{recipe_id}", response_class=HTMLResponse)
async def delete_recipe(
    recipe_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a recipe"""
    recipe = crud.delete_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return ""

# API Endpoints for frontend
@router.get("/api/search")
async def search_recipes(
    search: Optional[str] = None,
    tag_ids: Optional[str] = None,
    allergen_ids: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search recipes with filters (API endpoint)"""
    tag_id_list = [int(id) for id in tag_ids.split(",")] if tag_ids else None
    allergen_id_list = [int(id) for id in allergen_ids.split(",")] if allergen_ids else None

    recipes = crud.get_recipes(db, skip=skip, limit=limit, search=search, tag_ids=tag_id_list)

    if allergen_id_list:
        recipes = [
            recipe for recipe in recipes
            if not any(allergen.id in allergen_id_list for allergen in recipe.allergens)
        ]

    return recipes

@router.get("/api/ingredients/search")
async def search_ingredients(
    q: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Search ingredients with fuzzy matching for autocomplete"""
    if not q or len(q) < 1:
        return []

    # Fuzzy search now returns (ingredient, usage_count) tuples
    results = crud.search_ingredients_fuzzy(db, q, limit=limit)

    return [
        {
            "id": ingredient.id,
            "name": ingredient.name,
            "unit": ingredient.unit,
            "category": ingredient.category,
            "usage_count": usage_count
        }
        for ingredient, usage_count in results
    ]

@router.post("/api/ingredients/quick-create")
async def quick_create_ingredient(
    name: str = Form(...),
    unit: str = Form(...),
    category: str = Form("Sonstiges"),
    db: Session = Depends(get_db)
):
    """Quick create a new ingredient during recipe creation"""
    existing = db.query(models.Ingredient).filter(
        models.Ingredient.name == name
    ).first()

    if existing:
        return JSONResponse(
            status_code=400,
            content={"error": "Zutat existiert bereits", "ingredient": {
                "id": existing.id,
                "name": existing.name,
                "unit": existing.unit,
                "category": existing.category
            }}
        )

    ingredient_data = schemas.IngredientCreate(
        name=name,
        unit=unit,
        category=category
    )
    new_ingredient = crud.create_ingredient(db, ingredient_data)

    logger.info(f"Ingredient quick-created: {new_ingredient.name} (ID: {new_ingredient.id})")

    return {
        "id": new_ingredient.id,
        "name": new_ingredient.name,
        "unit": new_ingredient.unit,
        "category": new_ingredient.category,
        "usage_count": 0
    }
