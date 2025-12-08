from typing import Dict, Any
import json
from sqlalchemy.orm import Session

from app import crud

# Default conversion rules
DEFAULT_CONVERSIONS = {
    'g': {'threshold': 1000, 'target': 'kg', 'factor': 0.001},
    'ml': {'threshold': 1000, 'target': 'L', 'factor': 0.001},
    'mg': {'threshold': 1000, 'target': 'g', 'factor': 0.001},
}

def convert_unit(quantity: float, unit: str, custom_conversions: Dict = None) -> Dict[str, Any]:
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
        if quantity >= conv['threshold']:
            converted_quantity = quantity * conv['factor']
            
            # Round to reasonable precision
            if converted_quantity >= 10:
                converted_quantity = round(converted_quantity, 1)
            elif converted_quantity >= 1:
                converted_quantity = round(converted_quantity, 2)
            else:
                converted_quantity = round(converted_quantity, 3)
            
            return {
                'quantity': converted_quantity,
                'unit': conv['target'],
                'was_converted': True,
                'original_quantity': quantity,
                'original_unit': unit
            }
    
    # No conversion needed or possible
    return {
        'quantity': round(quantity, 2) if quantity != int(quantity) else int(quantity),
        'unit': unit,
        'was_converted': False
    }

def load_custom_conversions(db: Session) -> Dict:
    """Load custom conversion rules from database settings"""
    try:
        return crud.get_setting_value(db, 'unit_conversions', {})
    except Exception:
        return {}

def save_custom_conversions(db: Session, conversions: Dict):
    """Save custom conversion rules to database settings"""
    crud.set_setting_value(db, 'unit_conversions', conversions)

def add_custom_conversion(db: Session, from_unit: str, to_unit: str, threshold: float, factor: float):
    """Add a custom conversion rule"""
    conversions = load_custom_conversions(db)
    conversions[from_unit] = {
        'threshold': threshold,
        'target': to_unit,
        'factor': factor
    }
    save_custom_conversions(db, conversions)

def remove_custom_conversion(db: Session, from_unit: str):
    """Remove a custom conversion rule"""
    conversions = load_custom_conversions(db)
    if from_unit in conversions:
        del conversions[from_unit]
        save_custom_conversions(db, conversions)

def get_all_conversions(db: Session) -> Dict:
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
        return f"{quantity:.2f} {unit}".rstrip('0').rstrip('.')

def normalize_unit_name(unit: str) -> str:
    """Normalize unit names for consistency"""
    unit_mapping = {
        'gramm': 'g',
        'gram': 'g',
        'kilogramm': 'kg',
        'kilogram': 'kg',
        'liter': 'L',
        'milliliter': 'ml',
        'stück': 'Stück',
        'stueck': 'Stück',
        'piece': 'Stück',
        'pieces': 'Stück',
    }
    
    return unit_mapping.get(unit.lower(), unit)