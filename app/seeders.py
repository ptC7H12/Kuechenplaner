import logging

from app import crud
from app.database import SessionLocal

logger = logging.getLogger("kuechenplaner.seeders")


def init_default_data():
    """Initialize default tags, allergens and ingredients on first run."""
    db = SessionLocal()
    try:
        default_tags = [
            {"name": "Frühstück", "color": "#FCD34D", "icon": "🌅"},
            {"name": "Mittagessen", "color": "#F87171", "icon": "🍽️"},
            {"name": "Abendessen", "color": "#A78BFA", "icon": "🌙"},
            {"name": "Vegetarisch", "color": "#34D399", "icon": "🥬"},
            {"name": "Vegan", "color": "#10B981", "icon": "🌱"},
            {"name": "Glutenfrei", "color": "#F59E0B", "icon": "🌾"},
        ]
        for tag_data in default_tags:
            crud.get_or_create_tag(db, **tag_data)

        default_allergens = [
            {"name": "Gluten", "icon": "🌾"},
            {"name": "Milch", "icon": "🥛"},
            {"name": "Eier", "icon": "🥚"},
            {"name": "Nüsse", "icon": "🥜"},
            {"name": "Erdnüsse", "icon": "🥜"},
            {"name": "Soja", "icon": "🫘"},
            {"name": "Fisch", "icon": "🐟"},
            {"name": "Schalentiere", "icon": "🦐"},
            {"name": "Sellerie", "icon": "🥬"},
            {"name": "Senf", "icon": "🌭"},
            {"name": "Sesam", "icon": "🌰"},
            {"name": "Lupinen", "icon": "🌱"},
            {"name": "Schwefeldioxid", "icon": "⚠️"},
            {"name": "Weichtiere", "icon": "🦑"},
        ]
        for allergen_data in default_allergens:
            crud.get_or_create_allergen(db, **allergen_data)

        default_ingredients = [
            {"name": "Mehl", "unit": "g", "category": "Backwaren"},
            {"name": "Zucker", "unit": "g", "category": "Backwaren"},
            {"name": "Milch", "unit": "ml", "category": "Milchprodukte"},
            {"name": "Eier", "unit": "Stück", "category": "Milchprodukte"},
            {"name": "Kartoffeln", "unit": "kg", "category": "Gemüse"},
            {"name": "Zwiebeln", "unit": "kg", "category": "Gemüse"},
            {"name": "Tomaten", "unit": "kg", "category": "Gemüse"},
            {"name": "Äpfel", "unit": "kg", "category": "Obst"},
            {"name": "Bananen", "unit": "kg", "category": "Obst"},
            {"name": "Hackfleisch", "unit": "kg", "category": "Fleisch"},
            {"name": "Hähnchenbrust", "unit": "kg", "category": "Fleisch"},
            {"name": "Reis", "unit": "kg", "category": "Getreide"},
            {"name": "Nudeln", "unit": "kg", "category": "Getreide"},
            {"name": "Olivenöl", "unit": "ml", "category": "Öle & Fette"},
            {"name": "Salz", "unit": "g", "category": "Gewürze"},
            {"name": "Pfeffer", "unit": "g", "category": "Gewürze"},
        ]
        for ingredient_data in default_ingredients:
            crud.get_or_create_ingredient(db, **ingredient_data)

        db.commit()
        logger.info("Default data initialized successfully")
    finally:
        db.close()
