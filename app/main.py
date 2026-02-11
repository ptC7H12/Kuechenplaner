import uvicorn
from threading import Thread
import os
import logging
from contextlib import asynccontextmanager

# Setup logging first
from app.logging_config import setup_logging
setup_logging(log_level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("kuechenplaner.main")

# Only import webview if not in development mode
if not os.environ.get("DEVELOPMENT"):
    import webview
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import locale
from pathlib import Path

from app.database import create_tables, run_migrations, get_db, SessionLocal
from app.dependencies import get_current_camp, get_template_context, templates
from app import crud


def _init_default_data():
    """Initialize default tags, allergens and ingredients"""
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown"""
    logger.info("Application starting up...")

    # Set German locale for date formatting
    for locale_name in ('de_DE.UTF-8', 'de_DE', 'German'):
        try:
            locale.setlocale(locale.LC_TIME, locale_name)
            logger.info(f"Locale set to {locale_name}")
            break
        except locale.Error:
            continue
    else:
        logger.warning("Failed to set German locale, using default")

    create_tables()
    run_migrations()
    _init_default_data()

    logger.info("Application startup complete")
    yield
    logger.info("Application shutting down...")


# Import routers
from app.routers import camps
from app.routers import recipes as recipes_router
from app.routers import allergens
from app.routers import meal_planning
from app.routers import shopping_list
from app.routers import settings
from app.routers import export

app = FastAPI(title="Freizeit Rezepturverwaltung", version="1.0.0", lifespan=lifespan)

# Get the directory of this file
BASE_DIR = Path(__file__).parent

# Mount static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


# Global exception handler for SQLAlchemy errors
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Datenbankfehler. Bitte versuchen Sie es erneut."}
    )


# Root route - redirect to camp selection or dashboard
@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    current_camp=Depends(get_current_camp),
):
    if current_camp:
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        return RedirectResponse(url="/select-camp", status_code=302)

# Camp selection page
@app.get("/select-camp", response_class=HTMLResponse)
async def select_camp(
    context=Depends(get_template_context),
    db: Session = Depends(get_db)
):
    camps_list = crud.get_camps(db)
    last_selected_id = crud.get_setting_value(db, "last_selected_camp_id")
    last_selected_camp = None

    if last_selected_id:
        try:
            last_selected_camp = crud.get_camp(db, int(last_selected_id))
        except (ValueError, TypeError):
            pass

    return templates.TemplateResponse("camp_select.html", {
        **context,
        "camps": camps_list,
        "last_selected_camp": last_selected_camp
    })

# Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    context=Depends(get_template_context),
    db: Session = Depends(get_db)
):
    if not context["current_camp"]:
        return RedirectResponse(url="/select-camp", status_code=302)

    from app.services.calculation import get_camp_statistics
    stats = get_camp_statistics(db, context["current_camp"].id)

    return templates.TemplateResponse("dashboard.html", {
        **context,
        "stats": stats
    })

# Health check endpoint for startup detection
@app.get("/health")
async def health_check():
    return {"status": "ok"}


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
    logger.info("Starting FastAPI server on port 12000...")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=12000,
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

        # Wait for server to be ready via health check
        import urllib.request
        import time
        for _ in range(30):
            try:
                urllib.request.urlopen("http://127.0.0.1:12000/health", timeout=1)
                break
            except Exception:
                time.sleep(0.2)

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
