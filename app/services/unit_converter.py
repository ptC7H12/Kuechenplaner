import json
import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import crud

logger = logging.getLogger("kuechenplaner.unit_converter")

# Default conversion rules
DEFAULT_CONVERSIONS = {
    "g": {"threshold": 1000, "target": "kg", "factor": 0.001},
    "ml": {"threshold": 1000, "target": "L", "factor": 0.001},
    "mg": {"threshold": 1000, "target": "g", "factor": 0.001},
}

# Base-unit normalisation for mass / volume. Used by the shopping list to
# collapse the same ingredient across recipes that mix compatible units
# (e.g. 500 g + 2 kg → 2500 g → 2.5 kg after display conversion).
MASS_TO_BASE = {"kg": 1000.0, "g": 1.0, "mg": 0.001}
VOLUME_TO_BASE = {"L": 1000.0, "l": 1000.0, "ml": 1.0}


def normalize_to_base(quantity: float, unit: str) -> tuple[float, str]:
    """Convert mass/volume quantities to their base unit (g / ml).

    Returns (quantity, unit) unchanged for unknown / non-metric units
    (Stück, EL, TL, Packung, …) so they keep their own aggregation bucket.
    """
    if unit in MASS_TO_BASE:
        return quantity * MASS_TO_BASE[unit], "g"
    if unit in VOLUME_TO_BASE:
        return quantity * VOLUME_TO_BASE[unit], "ml"
    return quantity, unit


def convert_unit(quantity: float, unit: str, custom_conversions: dict = None) -> dict[str, Any]:
    """
    Convert units automatically based on quantity thresholds

    Args:
        quantity: The quantity to convert
        unit: The current unit
        custom_conversions: Optional custom conversion rules

    Returns:
        Dict with 'quantity' and 'unit' keys
    """

    # Merge default and custom conversions
    conversions = DEFAULT_CONVERSIONS.copy()
    if custom_conversions:
        conversions.update(custom_conversions)

    # Check if unit has a conversion rule
    if unit in conversions:
        conv = conversions[unit]
        if quantity >= conv["threshold"]:
            converted_quantity = quantity * conv["factor"]

            # Round to reasonable precision
            if converted_quantity >= 10:
                converted_quantity = round(converted_quantity, 1)
            elif converted_quantity >= 1:
                converted_quantity = round(converted_quantity, 2)
            else:
                converted_quantity = round(converted_quantity, 3)

            return {
                "quantity": converted_quantity,
                "unit": conv["target"],
                "was_converted": True,
                "original_quantity": quantity,
                "original_unit": unit,
            }

    # No conversion needed or possible
    return {
        "quantity": round(quantity, 2) if quantity != int(quantity) else int(quantity),
        "unit": unit,
        "was_converted": False,
    }


def load_custom_conversions(db: Session) -> dict:
    """Load custom conversion rules from database settings"""
    try:
        return crud.get_setting_value(db, "unit_conversions", {})
    except SQLAlchemyError as e:
        logger.warning("Failed to load custom unit conversions from DB: %s", e)
        return {}
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON in unit_conversions setting: %s", e)
        return {}


def save_custom_conversions(db: Session, conversions: dict):
    """Save custom conversion rules to database settings"""
    crud.set_setting_value(db, "unit_conversions", conversions)


def add_custom_conversion(db: Session, from_unit: str, to_unit: str, threshold: float, factor: float):
    """Add a custom conversion rule"""
    conversions = load_custom_conversions(db)
    conversions[from_unit] = {"threshold": threshold, "target": to_unit, "factor": factor}
    save_custom_conversions(db, conversions)


def remove_custom_conversion(db: Session, from_unit: str):
    """Remove a custom conversion rule"""
    conversions = load_custom_conversions(db)
    if from_unit in conversions:
        del conversions[from_unit]
        save_custom_conversions(db, conversions)


def get_all_conversions(db: Session) -> dict:
    """Get all conversion rules (default + custom)"""
    custom = load_custom_conversions(db)
    all_conversions = DEFAULT_CONVERSIONS.copy()
    all_conversions.update(custom)
    return all_conversions


def format_quantity_unit(quantity: float, unit: str) -> str:
    """Format quantity and unit for display"""
    if quantity == int(quantity):
        return f"{int(quantity)} {unit}"
    else:
        return f"{quantity:.2f} {unit}".rstrip("0").rstrip(".")


def _format_german_number(value: float) -> str:
    """Format a number with comma as decimal separator (German convention).

    One decimal place; integers render without trailing ',0'.
    """
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}".replace(".", ",")


def format_quantity_with_conversion(quantity: float, unit: str, custom_conversions: dict = None) -> str:
    """Convert (if applicable) and format a quantity for German-locale display.

    Used by PDF exports (recipe book, daily lists) so that 1500 g renders as
    "1,5 kg" rather than "1500.0 g". User-defined conversions (e.g. Becher -> ml)
    are applied when passed in. Falls back to the input unit when no conversion
    rule applies.
    """
    converted = convert_unit(quantity, unit, custom_conversions)
    return f"{_format_german_number(converted['quantity'])} {converted['unit']}"


def normalize_unit_name(unit: str) -> str:
    """Normalize unit names for consistency"""
    unit_mapping = {
        "gramm": "g",
        "gram": "g",
        "kilogramm": "kg",
        "kilogram": "kg",
        "liter": "L",
        "milliliter": "ml",
        "stück": "Stück",
        "stueck": "Stück",
        "piece": "Stück",
        "pieces": "Stück",
    }

    return unit_mapping.get(unit.lower(), unit)
