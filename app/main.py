import uvicorn
from threading import Thread
import os
import sys
import logging
from contextlib import asynccontextmanager

# In console-disabled Nuitka builds, sys.stdout/stderr can be None.
# Guard against AttributeError when anything tries to write to them.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

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

from app.database import run_migrations, backup_database, get_db, SessionLocal
from app.dependencies import get_current_camp, get_template_context, templates
from app import crud
from app.seeders import init_default_data


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

    backup_database()
    run_migrations()
    init_default_data()

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
from app.routers import leftovers

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
app.include_router(leftovers.router, prefix="/leftovers", tags=["leftovers"])

def start_server():
    """Start the FastAPI server"""
    logger.info("Starting FastAPI server on port 12000...")
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=12000,
            log_level="info"
        )
    except Exception:
        logger.exception("uvicorn crashed during startup")

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
        import platform
        server_ready = False
        for _ in range(60):  # up to ~72 s (covers slow first-run migrations)
            try:
                urllib.request.urlopen("http://127.0.0.1:12000/health", timeout=1)
                server_ready = True
                break
            except Exception:
                time.sleep(0.2)

        if not server_ready:
            if platform.system() == "Windows":
                log_path = Path(os.environ.get("APPDATA", "")) / "KuechenApp" / "logs" / "kuechenplaner.log"
            else:
                log_path = Path.home() / ".local" / "share" / "KuechenApp" / "logs" / "kuechenplaner.log"
            webview.create_window(
                "Startfehler – Freizeit Rezepturverwaltung",
                html=(
                    "<body style='font-family:sans-serif;padding:40px'>"
                    "<h2>Server konnte nicht gestartet werden</h2>"
                    f"<p>Log-Datei: <code>{log_path}</code></p>"
                    "</body>"
                ),
                width=700,
                height=250,
            )
            webview.start()
            return

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
