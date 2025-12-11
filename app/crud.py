from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime
import json

from app import models, schemas

# Camp CRUD operations
def get_camp(db: Session, camp_id: int):
    return db.query(models.Camp).filter(models.Camp.id == camp_id).first()

def get_camps(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Camp).order_by(models.Camp.last_accessed.desc()).offset(skip).limit(limit).all()

def create_camp(db: Session, camp: schemas.CampCreate):
    db_camp = models.Camp(**camp.dict())
    db.add(db_camp)
    db.commit()
    db.refresh(db_camp)
    return db_camp

def update_camp(db: Session, camp_id: int, camp_update: schemas.CampUpdate):
    db_camp = get_camp(db, camp_id)
    if db_camp:
        update_data = camp_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_camp, field, value)
        db_camp.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_camp)
    return db_camp

def delete_camp(db: Session, camp_id: int):
    db_camp = get_camp(db, camp_id)
    if db_camp:
        db.delete(db_camp)
        db.commit()
    return db_camp

def update_camp_last_accessed(db: Session, camp_id: int):
    db_camp = get_camp(db, camp_id)
    if db_camp:
        db_camp.last_accessed = datetime.utcnow()
        db.commit()
        db.refresh(db_camp)
    return db_camp

# Recipe CRUD operations
def get_recipe(db: Session, recipe_id: int):
    return db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()

def get_recipes(db: Session, skip: int = 0, limit: int = 100, search: str = None, tag_ids: List[int] = None):
    query = db.query(models.Recipe)
    
    if search:
        query = query.filter(or_(
            models.Recipe.name.contains(search),
            models.Recipe.description.contains(search)
        ))
    
    if tag_ids:
        query = query.join(models.Recipe.tags).filter(models.Tag.id.in_(tag_ids))
    
    return query.order_by(models.Recipe.updated_at.desc()).offset(skip).limit(limit).all()

def create_recipe(db: Session, recipe: schemas.RecipeCreate):
    # Create recipe
    recipe_data = recipe.dict(exclude={'ingredients', 'tag_ids', 'allergen_ids'})
    db_recipe = models.Recipe(**recipe_data)
    db.add(db_recipe)
    db.flush()  # Get the ID without committing

    # Add ingredients
    for ingredient_data in recipe.ingredients:
        db_recipe_ingredient = models.RecipeIngredient(
            recipe_id=db_recipe.id,
            **ingredient_data.dict()
        )
        db.add(db_recipe_ingredient)

    # Add tags
    if recipe.tag_ids:
        tags = db.query(models.Tag).filter(models.Tag.id.in_(recipe.tag_ids)).all()
        db_recipe.tags = tags

    # Add allergens
    if recipe.allergen_ids:
        allergens = db.query(models.Allergen).filter(models.Allergen.id.in_(recipe.allergen_ids)).all()
        db_recipe.allergens = allergens

    db.commit()
    db.refresh(db_recipe)

    # Create initial version
    _create_recipe_version(db, db_recipe)

    return db_recipe

def update_recipe(db: Session, recipe_id: int, recipe_update: schemas.RecipeUpdate):
    db_recipe = get_recipe(db, recipe_id)
    if not db_recipe:
        return None

    # Update basic fields
    update_data = recipe_update.dict(exclude_unset=True, exclude={'ingredients', 'tag_ids', 'allergen_ids'})
    for field, value in update_data.items():
        setattr(db_recipe, field, value)

    # Update ingredients if provided
    if recipe_update.ingredients is not None:
        # Delete existing ingredients
        db.query(models.RecipeIngredient).filter(models.RecipeIngredient.recipe_id == recipe_id).delete()

        # Add new ingredients
        for ingredient_data in recipe_update.ingredients:
            db_recipe_ingredient = models.RecipeIngredient(
                recipe_id=recipe_id,
                **ingredient_data.dict()
            )
            db.add(db_recipe_ingredient)

    # Update tags if provided
    if recipe_update.tag_ids is not None:
        tags = db.query(models.Tag).filter(models.Tag.id.in_(recipe_update.tag_ids)).all()
        db_recipe.tags = tags

    # Update allergens if provided
    if recipe_update.allergen_ids is not None:
        allergens = db.query(models.Allergen).filter(models.Allergen.id.in_(recipe_update.allergen_ids)).all()
        db_recipe.allergens = allergens

    # Increment version number
    db_recipe.version_number += 1
    db_recipe.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_recipe)

    # Create new version snapshot
    _create_recipe_version(db, db_recipe)

    return db_recipe

def delete_recipe(db: Session, recipe_id: int):
    db_recipe = get_recipe(db, recipe_id)
    if db_recipe:
        db.delete(db_recipe)
        db.commit()
    return db_recipe

# Ingredient CRUD operations
def get_ingredient(db: Session, ingredient_id: int):
    return db.query(models.Ingredient).filter(models.Ingredient.id == ingredient_id).first()

def get_ingredients(db: Session, skip: int = 0, limit: int = 100, search: str = None):
    query = db.query(models.Ingredient)
    if search:
        query = query.filter(models.Ingredient.name.contains(search))
    return query.order_by(models.Ingredient.name).offset(skip).limit(limit).all()

def create_ingredient(db: Session, ingredient: schemas.IngredientCreate):
    db_ingredient = models.Ingredient(**ingredient.dict())
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient

def get_or_create_ingredient(db: Session, name: str, unit: str, category: str):
    """Get existing ingredient or create new one"""
    db_ingredient = db.query(models.Ingredient).filter(models.Ingredient.name == name).first()
    if not db_ingredient:
        ingredient_data = schemas.IngredientCreate(name=name, unit=unit, category=category)
        db_ingredient = create_ingredient(db, ingredient_data)
    return db_ingredient

def search_ingredients_fuzzy(db: Session, query: str, limit: int = 10):
    """Search ingredients using fuzzy matching with usage count"""
    from thefuzz import fuzz
    from sqlalchemy import func

    if not query or len(query) < 1:
        return []

    # Get all ingredients with usage count
    ingredients_with_count = db.query(
        models.Ingredient,
        func.count(models.RecipeIngredient.id).label('usage_count')
    ).outerjoin(
        models.RecipeIngredient,
        models.Ingredient.id == models.RecipeIngredient.ingredient_id
    ).group_by(models.Ingredient.id).all()

    # Calculate fuzzy scores
    results = []
    query_lower = query.lower()

    for ingredient, usage_count in ingredients_with_count:
        name_lower = ingredient.name.lower()

        # Calculate different match scores
        exact_match = 100 if query_lower == name_lower else 0
        starts_with = 95 if name_lower.startswith(query_lower) else 0
        contains = 85 if query_lower in name_lower else 0
        fuzzy_score = fuzz.partial_ratio(query_lower, name_lower)

        # Best score wins
        best_score = max(exact_match, starts_with, contains, fuzzy_score)

        # Only include if score is reasonable
        if best_score >= 60:
            results.append({
                'ingredient': ingredient,
                'score': best_score,
                'usage_count': usage_count or 0
            })

    # Sort by score (desc), then by usage_count (desc), then by name (asc)
    results.sort(key=lambda x: (-x['score'], -x['usage_count'], x['ingredient'].name))

    # Return top N ingredients
    return [r['ingredient'] for r in results[:limit]]

# Tag CRUD operations
def get_tag(db: Session, tag_id: int):
    return db.query(models.Tag).filter(models.Tag.id == tag_id).first()

def get_tags(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Tag).order_by(models.Tag.name).offset(skip).limit(limit).all()

def create_tag(db: Session, tag: schemas.TagCreate):
    db_tag = models.Tag(**tag.dict())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def get_or_create_tag(db: Session, name: str, color: str = "#3B82F6", icon: str = None):
    """Get existing tag or create new one"""
    db_tag = db.query(models.Tag).filter(models.Tag.name == name).first()
    if not db_tag:
        tag_data = schemas.TagCreate(name=name, color=color, icon=icon)
        db_tag = create_tag(db, tag_data)
    return db_tag

# Meal Plan CRUD operations
def get_meal_plan(db: Session, meal_plan_id: int):
    return db.query(models.MealPlan).filter(models.MealPlan.id == meal_plan_id).first()

def get_meal_plans_for_camp(db: Session, camp_id: int):
    return db.query(models.MealPlan).filter(models.MealPlan.camp_id == camp_id).order_by(
        models.MealPlan.meal_date, models.MealPlan.meal_type, models.MealPlan.position
    ).all()

def create_meal_plan(db: Session, meal_plan: schemas.MealPlanCreate):
    # Get the next position for this meal slot
    existing_count = db.query(models.MealPlan).filter(
        and_(
            models.MealPlan.camp_id == meal_plan.camp_id,
            models.MealPlan.meal_date == meal_plan.meal_date,
            models.MealPlan.meal_type == meal_plan.meal_type
        )
    ).count()

    # Exclude position from the dict to avoid duplicate keyword argument
    meal_plan_data = meal_plan.dict(exclude={'position'})
    db_meal_plan = models.MealPlan(**meal_plan_data, position=existing_count)
    db.add(db_meal_plan)
    db.commit()
    db.refresh(db_meal_plan)
    return db_meal_plan

def update_meal_plan(db: Session, meal_plan_id: int, meal_plan_update: schemas.MealPlanUpdate):
    db_meal_plan = get_meal_plan(db, meal_plan_id)
    if db_meal_plan:
        update_data = meal_plan_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_meal_plan, field, value)
        db.commit()
        db.refresh(db_meal_plan)
    return db_meal_plan

def delete_meal_plan(db: Session, meal_plan_id: int):
    db_meal_plan = get_meal_plan(db, meal_plan_id)
    if db_meal_plan:
        db.delete(db_meal_plan)
        db.commit()
    return db_meal_plan

# App Settings CRUD operations
def get_setting(db: Session, key: str):
    return db.query(models.AppSettings).filter(models.AppSettings.key == key).first()

def set_setting(db: Session, key: str, value: str):
    db_setting = get_setting(db, key)
    if db_setting:
        db_setting.value = value
    else:
        db_setting = models.AppSettings(key=key, value=value)
        db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def get_setting_value(db: Session, key: str, default=None):
    """Get setting value, return default if not found"""
    setting = get_setting(db, key)
    if setting:
        try:
            return json.loads(setting.value)
        except json.JSONDecodeError:
            return setting.value
    return default

def set_setting_value(db: Session, key: str, value):
    """Set setting value, automatically JSON encode if needed"""
    if isinstance(value, (dict, list)):
        value_str = json.dumps(value)
    else:
        value_str = str(value)
    return set_setting(db, key, value_str)

# Allergen CRUD operations
def get_allergen(db: Session, allergen_id: int):
    return db.query(models.Allergen).filter(models.Allergen.id == allergen_id).first()

def get_allergens(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Allergen).order_by(models.Allergen.name).offset(skip).limit(limit).all()

def create_allergen(db: Session, allergen: schemas.AllergenCreate):
    db_allergen = models.Allergen(**allergen.dict())
    db.add(db_allergen)
    db.commit()
    db.refresh(db_allergen)
    return db_allergen

def get_or_create_allergen(db: Session, name: str, icon: str = None):
    """Get existing allergen or create new one"""
    db_allergen = db.query(models.Allergen).filter(models.Allergen.name == name).first()
    if not db_allergen:
        allergen_data = schemas.AllergenCreate(name=name, icon=icon)
        db_allergen = create_allergen(db, allergen_data)
    return db_allergen

# Recipe Version CRUD operations
def get_recipe_version(db: Session, version_id: int):
    return db.query(models.RecipeVersion).filter(models.RecipeVersion.id == version_id).first()

def get_recipe_versions(db: Session, recipe_id: int):
    """Get all versions for a recipe, ordered by version number descending"""
    return db.query(models.RecipeVersion).filter(
        models.RecipeVersion.recipe_id == recipe_id
    ).order_by(models.RecipeVersion.version_number.desc()).all()

def _create_recipe_version(db: Session, recipe: models.Recipe):
    """Internal function to create a version snapshot of a recipe"""
    # Create JSON snapshots
    ingredients_snapshot = json.dumps([
        {
            'ingredient_id': ri.ingredient_id,
            'ingredient_name': ri.ingredient.name,
            'quantity': ri.quantity,
            'unit': ri.unit
        }
        for ri in recipe.ingredients
    ])

    tags_snapshot = json.dumps([
        {'id': tag.id, 'name': tag.name, 'color': tag.color, 'icon': tag.icon}
        for tag in recipe.tags
    ])

    allergens_snapshot = json.dumps([
        {'id': allergen.id, 'name': allergen.name, 'icon': allergen.icon}
        for allergen in recipe.allergens
    ])

    # Create version record
    db_version = models.RecipeVersion(
        recipe_id=recipe.id,
        version_number=recipe.version_number,
        name=recipe.name,
        description=recipe.description,
        base_servings=recipe.base_servings,
        instructions=recipe.instructions,
        preparation_time=recipe.preparation_time,
        cooking_time=recipe.cooking_time,
        allergen_notes=recipe.allergen_notes,
        ingredients_snapshot=ingredients_snapshot,
        tags_snapshot=tags_snapshot,
        allergens_snapshot=allergens_snapshot
    )

    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version