import uvicorn
import webview
from threading import Thread
from fastapi import FastAPI, Request, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import os
import locale
from pathlib import Path
from datetime import datetime, timedelta

from app.database import create_tables, get_db
from app.dependencies import get_current_camp, get_template_context
from app import crud

# Import routers
from app.routers import camps
from app.routers import recipes as recipes_router
from app.routers import allergens
from app.routers import meal_planning
from app.routers import shopping_list
from app.routers import settings
from app.routers import export

app = FastAPI(title="Freizeit Rezepturverwaltung", version="1.0.0")

# Get the directory of this file
BASE_DIR = Path(__file__).parent

# Mount static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Templates
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    # Set German locale for date formatting
    try:
        locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    except locale.Error:
        try:
            # Try alternative German locale names
            locale.setlocale(locale.LC_TIME, 'de_DE')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'German')
            except locale.Error:
                # If all fail, continue without locale (will fall back to English)
                pass

    create_tables()

    # Initialize default settings and sample data
    db = next(get_db())
    try:
        # Create default tags if they don't exist
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

        # Create default allergens if they don't exist
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

        # Create default ingredient categories if needed
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
            existing = db.query(crud.models.Ingredient).filter_by(name=ingredient_data["name"]).first()
            if not existing:
                crud.create_ingredient(db, crud.schemas.IngredientCreate(**ingredient_data))
        
        db.commit()
    finally:
        db.close()

# Root route - redirect to camp selection or dashboard
@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    current_camp = Depends(get_current_camp),
    context = Depends(get_template_context)
):
    if current_camp:
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        return RedirectResponse(url="/select-camp", status_code=302)

# Camp selection page
@app.get("/select-camp", response_class=HTMLResponse)
async def select_camp(context = Depends(get_template_context)):
    camps = crud.get_camps(context["db"])
    last_selected_id = crud.get_setting_value(context["db"], "last_selected_camp_id")
    last_selected_camp = None
    
    if last_selected_id:
        try:
            last_selected_camp = crud.get_camp(context["db"], int(last_selected_id))
        except (ValueError, TypeError):
            pass
    
    return templates.TemplateResponse("camp_select.html", {
        **context,
        "camps": camps,
        "last_selected_camp": last_selected_camp
    })

# Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(context = Depends(get_template_context)):
    if not context["current_camp"]:
        return RedirectResponse(url="/select-camp", status_code=302)
    
    from app.services.calculation import get_camp_statistics
    stats = get_camp_statistics(context["db"], context["current_camp"].id)
    
    return templates.TemplateResponse("dashboard.html", {
        **context,
        "stats": stats
    })

# Include routers
app.include_router(camps.router, prefix="/api/camps", tags=["camps"])
app.include_router(recipes_router.router, prefix="/recipes", tags=["recipes"])
app.include_router(allergens.router, prefix="/api/allergens", tags=["allergens"])
app.include_router(meal_planning.router, prefix="/meal-planning", tags=["meal-planning"])
app.include_router(shopping_list.router, prefix="/shopping-list", tags=["shopping-list"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])
app.include_router(export.router, prefix="/export", tags=["export"])

def start_server():
    """Start the FastAPI server"""
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Allow external access for development
        port=12000,      # Use the provided port
        log_level="info"
    )

def main():
    """Main entry point for the application"""
    if os.environ.get("DEVELOPMENT"):
        # Development mode - just start the server
        start_server()
    else:
        # Production mode - start server in thread and create webview window
        Thread(target=start_server, daemon=True).start()
        
        # Give the server a moment to start
        import time
        time.sleep(2)
        
        webview.create_window(
            "Freizeit Rezepturverwaltung", 
            "http://127.0.0.1:12000", 
            width=1400, 
            height=900,
            resizable=True,
            shadow=True
        )
        webview.start()

if __name__ == "__main__":
    main()