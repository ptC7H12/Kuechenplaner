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
    recipe_data = recipe.dict(exclude={'ingredients', 'tag_ids'})
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
    
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

def update_recipe(db: Session, recipe_id: int, recipe_update: schemas.RecipeUpdate):
    db_recipe = get_recipe(db, recipe_id)
    if not db_recipe:
        return None
    
    # Update basic fields
    update_data = recipe_update.dict(exclude_unset=True, exclude={'ingredients', 'tag_ids'})
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
    
    db_recipe.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_recipe)
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
    
    db_meal_plan = models.MealPlan(**meal_plan.dict(), position=existing_count)
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