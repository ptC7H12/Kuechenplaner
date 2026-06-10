import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.constants import RECIPE_LIST_LIMIT
from app.database import get_db
from app.dependencies import get_current_camp, get_template_context, templates
from app.logging_config import get_logger
from app.services import unit_converter
from app.services.leftover_statistics import (
    count_recipe_leftover_entries,
    get_ingredient_breakdown,
    get_recipe_statistics,
)

logger = get_logger("recipes")

router = APIRouter()


def parse_recipe_form_data(ingredients: str, tag_ids: str, allergen_ids: str):
    """Parse JSON form data for recipe creation/update.

    Returns the recipe-ingredient objects, the tag/allergen id lists and the
    per-ingredient category updates (``(ingredient_id, category_id)`` pairs for
    every ingredient whose payload carries a ``category_id`` key). The category
    is persisted on the *global* ``Ingredient`` row, not on the recipe link.
    """
    try:
        ingredients_list = json.loads(ingredients)
        tag_ids_list = json.loads(tag_ids)
        allergen_ids_list = json.loads(allergen_ids)

        ingredient_objects = [schemas.RecipeIngredientCreate(**ing) for ing in ingredients_list]

        category_updates = [
            (ing["ingredient_id"], ing["category_id"]) for ing in ingredients_list if "category_id" in ing
        ]

        return ingredient_objects, tag_ids_list, allergen_ids_list, category_updates

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Ungültige JSON-Daten: {str(e)}") from e
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Ungültige Zutatendaten: {str(e)}") from e


def apply_ingredient_category_updates(db: Session, category_updates: list[tuple[int, int | None]]):
    """Persist category changes made in the recipe form onto the global ingredients."""
    for ingredient_id, category_id in category_updates:
        crud.update_ingredient(db, ingredient_id, schemas.IngredientUpdate(category_id=category_id))


@router.get("/", response_class=HTMLResponse)
async def list_recipes(
    request: Request,
    search: str | None = None,
    tags: str | None = None,
    context: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
):
    """List all recipes with optional filtering"""
    recipes = crud.get_recipes(db, skip=0, limit=RECIPE_LIST_LIMIT)
    all_tags = crud.get_tags(db)
    all_allergens = crud.get_allergens(db)

    context.update(
        {
            "recipes": recipes,
            "tags": all_tags,
            "allergens": all_allergens,
            "search": search or "",
            "selected_tags": tags.split(",") if tags else [],
        }
    )

    return templates.TemplateResponse("recipes/list.html", context)


@router.get("/create", response_class=HTMLResponse)
async def create_recipe_form(
    request: Request, context: dict = Depends(get_template_context), db: Session = Depends(get_db)
):
    """Show create recipe form"""
    ingredients = crud.get_ingredients(db)
    tags = crud.get_tags(db)
    allergens = crud.get_allergens(db)
    categories = crud.get_categories(db)
    custom_units = list(unit_converter.load_custom_conversions(db).keys())

    context.update(
        {
            "ingredients": ingredients,
            "tags": tags,
            "allergens": allergens,
            "categories": categories,
            "custom_units": custom_units,
        }
    )

    return templates.TemplateResponse("recipes/create.html", context)


@router.post("/", response_class=HTMLResponse)
async def create_recipe(
    request: Request,
    name: str = Form(...),
    description: str | None = Form(None),
    base_servings: int = Form(...),
    instructions: str = Form(...),
    preparation_time: int | None = Form(None),
    cooking_time: int | None = Form(None),
    ingredients: str = Form(...),  # JSON string
    tag_ids: str = Form("[]"),  # JSON string
    allergen_ids: str = Form("[]"),  # JSON string
    db: Session = Depends(get_db),
):
    """Create a new recipe"""
    ingredient_objects, tag_ids_list, allergen_ids_list, category_updates = parse_recipe_form_data(
        ingredients, tag_ids, allergen_ids
    )

    recipe_data = schemas.RecipeCreate(
        name=name,
        description=description,
        base_servings=base_servings,
        instructions=instructions,
        preparation_time=preparation_time,
        cooking_time=cooking_time,
        ingredients=ingredient_objects,
        tag_ids=tag_ids_list,
        allergen_ids=allergen_ids_list,
    )

    recipe = crud.create_recipe(db, recipe_data)
    apply_ingredient_category_updates(db, category_updates)
    logger.info(f"Recipe created: {recipe.name} (ID: {recipe.id})")

    return RedirectResponse(url=f"/recipes/{recipe.id}", status_code=303)


@router.get("/{recipe_id}", response_class=HTMLResponse)
async def get_recipe(
    recipe_id: int,
    request: Request,
    context: dict = Depends(get_template_context),
    current_camp: models.Camp | None = Depends(get_current_camp),
    db: Session = Depends(get_db),
):
    """Get recipe details with optional leftover history (Story 8)."""
    recipe = crud.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    camp_id = current_camp.id if current_camp else None
    leftover_stats = get_recipe_statistics(db, recipe_id, current_camp_id=camp_id)
    ingredient_breakdown = get_ingredient_breakdown(db, recipe_id)
    leftover_total_entries = count_recipe_leftover_entries(db, recipe_id)

    context.update(
        {
            "recipe": recipe,
            "leftover_stats": leftover_stats,
            "leftover_ingredient_breakdown": ingredient_breakdown,
            "leftover_total_entries": leftover_total_entries,
        }
    )
    return templates.TemplateResponse("recipes/detail.html", context)


@router.get("/{recipe_id}/preview", response_class=HTMLResponse)
async def recipe_preview_fragment(
    recipe_id: int,
    request: Request,
    servings: int | None = None,
    context: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
):
    """HTML fragment for the recipe-preview modal in meal planning.

    Loaded via FreizeitApp.openModal() into #modal-content. Optionally scales
    ingredient quantities to the given servings (e.g. camp.participant_count
    or a MealPlan.custom_servings override).
    """
    recipe = crud.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    target_servings = servings if servings and servings > 0 else recipe.base_servings
    factor = target_servings / recipe.base_servings if recipe.base_servings > 0 else 1.0
    scaled_ingredients = [
        {
            "name": ri.ingredient.name,
            "quantity": ri.quantity * factor,
            "unit": ri.unit,
        }
        for ri in recipe.ingredients
    ]

    context.update(
        {
            "recipe": recipe,
            "scaled_ingredients": scaled_ingredients,
            "target_servings": target_servings,
            "scaling_factor": factor,
        }
    )
    return templates.TemplateResponse("recipes/preview_modal.html", context)


@router.get("/{recipe_id}/edit", response_class=HTMLResponse)
async def edit_recipe_form(
    recipe_id: int, request: Request, context: dict = Depends(get_template_context), db: Session = Depends(get_db)
):
    """Show edit recipe form"""
    recipe = crud.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    tags = crud.get_tags(db)
    allergens = crud.get_allergens(db)
    categories = crud.get_categories(db)
    custom_units = list(unit_converter.load_custom_conversions(db).keys())

    context.update(
        {
            "recipe": recipe,
            "tags": tags,
            "allergens": allergens,
            "categories": categories,
            "custom_units": custom_units,
        }
    )

    return templates.TemplateResponse("recipes/edit.html", context)


@router.put("/{recipe_id}", response_class=HTMLResponse)
async def update_recipe(
    recipe_id: int,
    request: Request,
    name: str = Form(...),
    description: str | None = Form(None),
    base_servings: int = Form(...),
    instructions: str = Form(...),
    preparation_time: int | None = Form(None),
    cooking_time: int | None = Form(None),
    ingredients: str = Form(...),  # JSON string
    tag_ids: str = Form("[]"),  # JSON string
    allergen_ids: str = Form("[]"),  # JSON string
    db: Session = Depends(get_db),
):
    """Update an existing recipe"""
    existing_recipe = crud.get_recipe(db, recipe_id)
    if not existing_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    ingredient_objects, tag_ids_list, allergen_ids_list, category_updates = parse_recipe_form_data(
        ingredients, tag_ids, allergen_ids
    )

    recipe_update = schemas.RecipeUpdate(
        name=name,
        description=description,
        base_servings=base_servings,
        instructions=instructions,
        preparation_time=preparation_time,
        cooking_time=cooking_time,
        ingredients=ingredient_objects,
        tag_ids=tag_ids_list,
        allergen_ids=allergen_ids_list,
    )

    updated_recipe = crud.update_recipe(db, recipe_id, recipe_update)
    apply_ingredient_category_updates(db, category_updates)
    logger.info(f"Recipe updated: {updated_recipe.name} (ID: {recipe_id})")

    return RedirectResponse(url=f"/recipes/{recipe_id}", status_code=303)


@router.get("/{recipe_id}/versions", response_class=HTMLResponse)
async def get_recipe_versions(
    recipe_id: int, request: Request, context: dict = Depends(get_template_context), db: Session = Depends(get_db)
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

    context.update({"recipe": recipe, "versions": versions, "current_version": recipe.version_number})

    return templates.TemplateResponse("recipes/versions.html", context)


@router.delete("/{recipe_id}", response_class=HTMLResponse)
async def delete_recipe(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    """Delete a recipe"""
    recipe = crud.delete_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return ""


# API Endpoints for frontend
@router.get("/api/search")
async def search_recipes(
    search: str | None = None,
    tag_ids: str | None = None,
    allergen_ids: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Search recipes with filters (API endpoint)"""
    tag_id_list = [int(id) for id in tag_ids.split(",")] if tag_ids else None
    allergen_id_list = [int(id) for id in allergen_ids.split(",")] if allergen_ids else None

    recipes = crud.get_recipes(db, skip=skip, limit=limit, search=search, tag_ids=tag_id_list)

    if allergen_id_list:
        recipes = [
            recipe for recipe in recipes if not any(allergen.id in allergen_id_list for allergen in recipe.allergens)
        ]

    return recipes


@router.get("/api/ingredients/search")
async def search_ingredients(q: str, limit: int = 10, db: Session = Depends(get_db)):
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
            "category": ingredient.category.name if ingredient.category else "",
            "category_id": ingredient.category_id,
            "usage_count": usage_count,
        }
        for ingredient, usage_count in results
    ]


@router.post("/api/ingredients/quick-create")
async def quick_create_ingredient(
    name: str = Form(...), unit: str = Form(...), category: str = Form("Sonstiges"), db: Session = Depends(get_db)
):
    """Quick create a new ingredient during recipe creation"""
    existing = crud.get_ingredient_by_name(db, name)

    if existing:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Zutat existiert bereits",
                "ingredient": {
                    "id": existing.id,
                    "name": existing.name,
                    "unit": existing.unit,
                    "category": existing.category.name if existing.category else "",
                    "category_id": existing.category_id,
                },
            },
        )

    db_category = crud.get_or_create_category(db, category) if category else None
    ingredient_data = schemas.IngredientCreate(
        name=name, unit=unit, category_id=db_category.id if db_category else None
    )
    new_ingredient = crud.create_ingredient(db, ingredient_data)

    logger.info(f"Ingredient quick-created: {new_ingredient.name} (ID: {new_ingredient.id})")

    return {
        "id": new_ingredient.id,
        "name": new_ingredient.name,
        "unit": new_ingredient.unit,
        "category": db_category.name if db_category else "",
        "category_id": db_category.id if db_category else None,
        "usage_count": 0,
    }
