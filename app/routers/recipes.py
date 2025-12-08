from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.dependencies import get_current_camp, get_template_context
from app import crud, schemas

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
    
    # Get all tags for filter dropdown
    all_tags = crud.get_tags(db)
    
    context.update({
        "recipes": recipes,
        "tags": all_tags,
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
    instructions: Optional[str] = Form(None),
    preparation_time: Optional[int] = Form(None),
    cooking_time: Optional[int] = Form(None),
    allergens: Optional[str] = Form(None),
    allergen_notes: Optional[str] = Form(None),
    context: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    """Create a new recipe"""
    
    try:
        recipe_data = schemas.RecipeCreate(
            name=name,
            description=description,
            base_servings=base_servings,
            instructions=instructions,
            preparation_time=preparation_time,
            cooking_time=cooking_time,
            allergens=allergens,
            allergen_notes=allergen_notes
        )
        
        recipe = crud.create_recipe(db, recipe_data)
        
        # Return the new recipe card HTML
        context.update({"recipe": recipe})
        return templates.TemplateResponse("recipes/partials/recipe_card.html", context)
        
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