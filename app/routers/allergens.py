from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas

router = APIRouter()

@router.get("/")
async def list_allergens(db: Session = Depends(get_db)):
    """List all allergens"""
    return crud.get_allergens(db)

@router.get("/{allergen_id}")
async def get_allergen(allergen_id: int, db: Session = Depends(get_db)):
    """Get a specific allergen"""
    allergen = crud.get_allergen(db, allergen_id)
    if not allergen:
        raise HTTPException(status_code=404, detail="Allergen not found")
    return allergen

@router.post("/", status_code=201)
async def create_allergen(
    allergen: schemas.AllergenCreate,
    db: Session = Depends(get_db)
):
    """Create a new allergen"""
    return crud.create_allergen(db, allergen)
