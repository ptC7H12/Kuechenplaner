"""Tests for the pure-function helpers in `app.services.unit_converter`.

These never touch the DB — they exercise the conversion rules directly.
"""

from app.services.unit_converter import (
    convert_unit,
    format_quantity_unit,
    format_quantity_with_conversion,
    normalize_to_base,
    normalize_unit_name,
)


def test_grams_above_threshold_convert_to_kg():
    result = convert_unit(1500, "g")
    assert result["was_converted"] is True
    assert result["unit"] == "kg"
    assert result["quantity"] == 1.5
    assert result["original_quantity"] == 1500


def test_grams_below_threshold_stay_as_grams():
    result = convert_unit(500, "g")
    assert result["was_converted"] is False
    assert result["unit"] == "g"
    assert result["quantity"] == 500


def test_milliliters_above_threshold_convert_to_liters():
    result = convert_unit(2500, "ml")
    assert result["was_converted"] is True
    assert result["unit"] == "L"
    assert result["quantity"] == 2.5


def test_unknown_unit_passes_through():
    result = convert_unit(7, "Stück")
    assert result["was_converted"] is False
    assert result["unit"] == "Stück"
    assert result["quantity"] == 7


def test_custom_conversion_overrides_default():
    custom = {"g": {"threshold": 100, "target": "dag", "factor": 0.1}}
    result = convert_unit(200, "g", custom_conversions=custom)
    assert result["was_converted"] is True
    assert result["unit"] == "dag"
    assert result["quantity"] == 20.0


def test_format_quantity_unit_renders_integers_without_decimals():
    # Whole numbers render via int branch — no decimal point.
    assert format_quantity_unit(1.0, "kg") == "1 kg"
    # Non-whole numbers currently render with .2f; the rstrip('0').rstrip('.')
    # in the implementation acts on the *whole* string, so the unit suffix
    # blocks zero-stripping. Locking in the current behavior here — flip this
    # test if the formatter is fixed to strip zeros before the unit.
    assert format_quantity_unit(1.5, "kg") == "1.50 kg"


def test_format_quantity_with_conversion_applies_custom_rule():
    # PDF exports (recipe book / daily lists) must honour user-defined
    # conversions, e.g. Becher -> ml.
    custom = {"Becher": {"threshold": 1, "target": "ml", "factor": 250}}
    assert format_quantity_with_conversion(4, "Becher", custom) == "1000 ml"


def test_format_quantity_with_conversion_without_custom_keeps_unit():
    assert format_quantity_with_conversion(4, "Becher") == "4 Becher"


def test_normalize_unit_name_maps_known_synonyms():
    assert normalize_unit_name("gramm") == "g"
    assert normalize_unit_name("Kilogramm") == "kg"
    assert normalize_unit_name("Stueck") == "Stück"


def test_normalize_unit_name_keeps_unknown_units():
    assert normalize_unit_name("Bund") == "Bund"


def test_normalize_to_base_mass_units():
    assert normalize_to_base(2.0, "kg") == (2000.0, "g")
    assert normalize_to_base(500, "g") == (500, "g")
    assert normalize_to_base(750, "mg") == (0.75, "g")


def test_normalize_to_base_volume_units():
    assert normalize_to_base(1.5, "L") == (1500.0, "ml")
    assert normalize_to_base(250, "ml") == (250, "ml")
    # Lower-case "l" is accepted as litre as well — recipe data is inconsistent.
    assert normalize_to_base(2, "l") == (2000.0, "ml")


def test_normalize_to_base_passes_through_unknown_units():
    assert normalize_to_base(5, "Stück") == (5, "Stück")
    assert normalize_to_base(3, "EL") == (3, "EL")
    assert normalize_to_base(1, "Packung") == (1, "Packung")
