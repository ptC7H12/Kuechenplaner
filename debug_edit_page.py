"""Debug script to check what data is rendered in the edit page"""

import sys
sys.path.insert(0, '/home/user/Kuechenplaner')
 

from app.database import SessionLocal
from app import crud
 
db = SessionLocal()
recipe = crud.get_recipe(db, 3)
 
if recipe:
    print(f"✓ Recipe loaded: {recipe.name}")
    print(f"  Description: {recipe.description}")
    print(f"  Base servings: {recipe.base_servings}")
    print(f"  Preparation time: {recipe.preparation_time}")
    print(f"  Cooking time: {recipe.cooking_time}")
    print(f"  Instructions length: {len(recipe.instructions) if recipe.instructions else 0}")
    print(f"  Allergen notes: {recipe.allergen_notes}")
    print(f"\n✓ Ingredients ({len(recipe.ingredients)}):")
    for ri in recipe.ingredients:
        print(f"    - {ri.ingredient.name}: {ri.quantity} {ri.unit} (Category: {ri.ingredient.category})")
    print(f"\n✓ Tags ({len(recipe.tags)}):")
    for tag in recipe.tags:
        print(f"    - {tag.name} (ID: {tag.id})")
 
    # Simulate what the template would generate
    print("\n--- SIMULATED RECIPE_DATA JavaScript Object ---")
    print("const RECIPE_DATA = {")
    print(f"    id: {recipe.id},")
    print(f'    name: "{recipe.name}",')
    print(f"    base_servings: {recipe.base_servings},")
    print(f"    ingredients: [")
    for ri in recipe.ingredients:
        print(f"        {{ ingredient_id: {ri.ingredient.id}, name: \"{ri.ingredient.name}\", quantity: {ri.quantity}, unit: \"{ri.unit}\", category: \"{ri.ingredient.category}\" }},")
    print(f"    ],")
    print(f"    tag_ids: [{', '.join(str(tag.id) for tag in recipe.tags)}]")
    print("};")
else:
    print("✗ Recipe not found!")
 
db.close()
