from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.dependencies import get_current_camp, get_template_context
from app import crud, schemas, models

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_recipes(
    request: Request,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    context: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    """List all recipes with optional filtering"""

    # Get all recipes (for now, without filtering)
    recipes = crud.get_recipes(db, skip=0, limit=100)

    # Get all tags and allergens for filter dropdowns
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
    
    # Get all ingredients and tags for the form
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
    context: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    """Create a new recipe"""

    try:
        import json

        # Parse JSON strings
        ingredients_list = json.loads(ingredients)
        tag_ids_list = json.loads(tag_ids)

        # Convert ingredients to RecipeIngredientCreate objects
        ingredient_objects = [
            schemas.RecipeIngredientCreate(**ing) for ing in ingredients_list
        ]

        # Create recipe data
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

        # Create recipe in database
        recipe = crud.create_recipe(db, recipe_data)

        # Redirect to recipe detail page
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/recipes/{recipe.id}", status_code=303)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    """Show edit recipe form (redirects to detail for now)"""

    recipe = crud.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # For now, redirect to detail page
    # TODO: Implement proper edit form
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/recipes/{recipe_id}", status_code=302)

@router.put("/{recipe_id}")
async def update_recipe(
    recipe_id: int,
    recipe_update: schemas.RecipeUpdate,
    db: Session = Depends(get_db)
):
    """Update a recipe (API endpoint)"""

    recipe = crud.update_recipe(db, recipe_id, recipe_update)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return recipe

@router.get("/{recipe_id}/versions")
async def get_recipe_versions(
    recipe_id: int,
    db: Session = Depends(get_db)
):
    """Get all versions of a recipe"""

    recipe = crud.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    versions = crud.get_recipe_versions(db, recipe_id)
    return {
        "recipe": recipe,
        "versions": versions,
        "current_version": recipe.version_number
    }

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

    # Return empty response (HTMX will remove the element)
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

    # Parse tag_ids and allergen_ids from comma-separated string
    tag_id_list = [int(id) for id in tag_ids.split(",")] if tag_ids else None
    allergen_id_list = [int(id) for id in allergen_ids.split(",")] if allergen_ids else None

    recipes = crud.get_recipes(db, skip=skip, limit=limit, search=search, tag_ids=tag_id_list)

    # Filter by allergens if provided (exclude recipes with these allergens)
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

    # Use fuzzy search from crud
    ingredients = crud.search_ingredients_fuzzy(db, q, limit=limit)

    # Calculate usage count for each ingredient
    from sqlalchemy import func
    usage_counts = {}
    for ingredient in ingredients:
        count = db.query(func.count(models.RecipeIngredient.id)).filter(
            models.RecipeIngredient.ingredient_id == ingredient.id
        ).scalar()
        usage_counts[ingredient.id] = count

    # Return formatted results
    return [
        {
            "id": ingredient.id,
            "name": ingredient.name,
            "unit": ingredient.unit,
            "category": ingredient.category,
            "usage_count": usage_counts.get(ingredient.id, 0)
        }
        for ingredient in ingredients
    ]

@router.post("/api/ingredients/quick-create")
async def quick_create_ingredient(
    name: str = Form(...),
    unit: str = Form(...),
    category: str = Form("Sonstiges"),
    db: Session = Depends(get_db)
):
    """Quick create a new ingredient during recipe creation"""

    try:
        # Check if ingredient already exists
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

        # Create new ingredient
        ingredient_data = schemas.IngredientCreate(
            name=name,
            unit=unit,
            category=category
        )
        new_ingredient = crud.create_ingredient(db, ingredient_data)

        return {
            "id": new_ingredient.id,
            "name": new_ingredient.name,
            "unit": new_ingredient.unit,
            "category": new_ingredient.category,
            "usage_count": 0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))