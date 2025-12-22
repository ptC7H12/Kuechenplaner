from sqlalchemy.orm import Session, selectinload
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from app import models, crud
from app.services.unit_converter import convert_unit

logger = logging.getLogger("kuechenplaner.calculation")

def scale_recipe(recipe: models.Recipe, target_servings: int) -> Dict[str, Any]:
    """Scale recipe ingredients to target servings"""
    if recipe.base_servings <= 0:
        raise ValueError("Recipe base_servings must be greater than 0")
    
    factor = target_servings / recipe.base_servings
    
    scaled_ingredients = []
    for recipe_ingredient in recipe.ingredients:
        scaled_ingredients.append({
            'ingredient': recipe_ingredient.ingredient,
            'quantity': recipe_ingredient.quantity * factor,
            'unit': recipe_ingredient.unit,
            'original_quantity': recipe_ingredient.quantity,
            'original_unit': recipe_ingredient.unit
        })
    
    return {
        'recipe': recipe,
        'ingredients': scaled_ingredients,
        'factor': factor,
        'target_servings': target_servings,
        'base_servings': recipe.base_servings
    }

def calculate_shopping_list(db: Session, camp_id: int) -> Dict[str, Any]:
    """Calculate aggregated shopping list for a camp"""
    
    # Get camp and meal plans
    camp = crud.get_camp(db, camp_id)
    if not camp:
        raise ValueError(f"Camp with id {camp_id} not found")
    
    meal_plans = crud.get_meal_plans_for_camp(db, camp_id)
    
    # Aggregate ingredients
    aggregated = defaultdict(lambda: {'quantity': 0, 'ingredient': None, 'unit': None})
    
    for meal_plan in meal_plans:
        # Skip "no meal" entries (recipe_id is NULL)
        if not meal_plan.recipe_id or not meal_plan.recipe:
            continue

        scaled = scale_recipe(meal_plan.recipe, camp.participant_count)

        for ingredient_data in scaled['ingredients']:
            ingredient = ingredient_data['ingredient']
            quantity = ingredient_data['quantity']
            unit = ingredient_data['unit']

            # Use ingredient ID and unit as key for aggregation
            key = (ingredient.id, unit)

            if aggregated[key]['ingredient'] is None:
                aggregated[key]['ingredient'] = ingredient
                aggregated[key]['unit'] = unit

            aggregated[key]['quantity'] += quantity
    
    # Convert to list and apply unit conversions
    shopping_items = []
    for (ingredient_id, unit), data in aggregated.items():
        converted = convert_unit(data['quantity'], data['unit'])
        
        shopping_items.append({
            'ingredient': data['ingredient'],
            'quantity': converted['quantity'],
            'unit': converted['unit'],
            'original_quantity': data['quantity'],
            'original_unit': data['unit'],
            'category': data['ingredient'].category
        })
    
    # Group by category
    categories = defaultdict(list)
    for item in shopping_items:
        categories[item['category']].append(item)
    
    # Sort categories and items within categories
    sorted_categories = {}
    for category in sorted(categories.keys()):
        sorted_categories[category] = sorted(
            categories[category], 
            key=lambda x: x['ingredient'].name
        )
    
    return {
        'camp': camp,
        'items': shopping_items,
        'categories': sorted_categories,
        'total_items': len(shopping_items),
        'total_recipes': len(set(mp.recipe_id for mp in meal_plans))
    }

def get_camp_statistics(db: Session, camp_id: int) -> Dict[str, Any]:
    """Get statistics for a camp"""
    
    camp = crud.get_camp(db, camp_id)
    if not camp:
        return {}
    
    meal_plans = crud.get_meal_plans_for_camp(db, camp_id)
    
    # Count meals by type
    meal_counts = defaultdict(int)
    recipe_ids = set()

    for meal_plan in meal_plans:
        meal_counts[meal_plan.meal_type.value] += 1
        # Only count actual recipes (not "no meal" entries)
        if meal_plan.recipe_id:
            recipe_ids.add(meal_plan.recipe_id)
    
    # Calculate total days
    total_days = (camp.end_date - camp.start_date).days + 1

    # Calculate expected meals (3 per day)
    expected_meals = total_days * 3

    # Count unique meal slots that have at least one MealPlan entry
    # (includes both recipes and "no meal" markers, as both are conscious planning decisions)
    meal_slots_with_plans = set()
    for meal_plan in meal_plans:
        meal_slots_with_plans.add((meal_plan.meal_date.date(), meal_plan.meal_type))

    planned_meals = len(meal_slots_with_plans)
    
    # Check for missing meals
    warnings = []
    if planned_meals < expected_meals:
        warnings.append(f"{expected_meals - planned_meals} Mahlzeiten noch nicht geplant")
    
    # Check for recipes without allergen information (optimized bulk query)
    recipes_without_allergens = 0
    if recipe_ids:
        # Bulk query instead of N+1 queries
        recipes_to_check = db.query(models.Recipe).filter(
            models.Recipe.id.in_(recipe_ids)
        ).options(selectinload(models.Recipe.allergens)).all()

        recipes_without_allergens = sum(1 for r in recipes_to_check if not r.allergens)

        if recipes_without_allergens > 0:
            warnings.append(f"{recipes_without_allergens} Rezepte ohne Allergen-Informationen")

    # Create daily overview
    daily_overview = []
    current_date = camp.start_date

    for day_num in range(total_days):
        day_date = current_date + timedelta(days=day_num)

        # Get meals for this day
        day_meals = {
            'BREAKFAST': None,
            'LUNCH': None,
            'DINNER': None
        }

        for meal_plan in meal_plans:
            # Compare only the date part
            if meal_plan.meal_date.date() == day_date.date():
                meal_type_str = meal_plan.meal_type.value
                if day_meals[meal_type_str] is None:
                    day_meals[meal_type_str] = []
                day_meals[meal_type_str].append(meal_plan)

        # Count planned meals for this day (includes "no meal" markers as planned decisions)
        meals_planned = sum(1 for meals in day_meals.values() if meals is not None and len(meals) > 0)

        daily_overview.append({
            'day_number': day_num + 1,
            'date': day_date,
            'meals': day_meals,
            'meals_planned': meals_planned
        })

    return {
        'camp': camp,
        'total_days': total_days,
        'planned_meals': planned_meals,
        'expected_meals': expected_meals,
        'unique_recipes': len(recipe_ids),
        'meal_counts': dict(meal_counts),
        'completion_percentage': round((planned_meals / expected_meals) * 100, 1) if expected_meals > 0 else 0,
        'warnings': warnings,
        'daily_overview': daily_overview
    }