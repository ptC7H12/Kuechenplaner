from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.Allergen])
async def get_allergens(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all allergens"""
    return crud.get_allergens(db, skip=skip, limit=limit)

@router.get("/{allergen_id}", response_model=schemas.Allergen)
async def get_allergen(
    allergen_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific allergen"""
    allergen = crud.get_allergen(db, allergen_id)
    if not allergen:
        raise HTTPException(status_code=404, detail="Allergen not found")
    return allergen

@router.post("/", response_model=schemas.Allergen)
async def create_allergen(
    allergen: schemas.AllergenCreate,
    db: Session = Depends(get_db)
):
    """Create a new allergen"""
    return crud.create_allergen(db, allergen)
