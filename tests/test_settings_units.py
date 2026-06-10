"""Tests for Story 31: custom unit conversion add/list/delete endpoints."""

from __future__ import annotations

from app.services import unit_converter


def test_add_conversion_persists_and_renders(client, db_session):
    response = client.post(
        "/settings/api/settings/units/conversions/add",
        data={"from_unit": "Becher", "to_unit": "ml", "factor": "250"},
    )

    assert response.status_code == 200
    assert "Becher" in response.text
    assert "250" in response.text

    db_session.expire_all()
    stored = unit_converter.load_custom_conversions(db_session)
    assert stored["Becher"] == {"threshold": 1, "target": "ml", "factor": 250.0}


def test_add_conversion_rejects_invalid_factor(client, db_session):
    response = client.post(
        "/settings/api/settings/units/conversions/add",
        data={"from_unit": "Becher", "to_unit": "ml", "factor": "0"},
    )

    assert response.status_code == 400
    db_session.expire_all()
    assert unit_converter.load_custom_conversions(db_session) == {}


def test_add_conversion_rejects_missing_field(client, db_session):
    response = client.post(
        "/settings/api/settings/units/conversions/add",
        data={"from_unit": "Becher", "to_unit": "", "factor": "250"},
    )

    assert response.status_code == 400
    db_session.expire_all()
    assert unit_converter.load_custom_conversions(db_session) == {}


def test_delete_conversion_removes_entry(client, db_session):
    client.post(
        "/settings/api/settings/units/conversions/add",
        data={"from_unit": "Becher", "to_unit": "ml", "factor": "250"},
    )

    response = client.delete("/settings/api/settings/units/conversions/Becher")

    assert response.status_code == 200
    assert "Keine benutzerdefinierten Konvertierungen" in response.text

    db_session.expire_all()
    assert unit_converter.load_custom_conversions(db_session) == {}


def test_empty_initial_list_renders_fallback(client):
    # Deleting a non-existent conversion is a no-op and renders the empty state.
    response = client.delete("/settings/api/settings/units/conversions/Unbekannt")

    assert response.status_code == 200
    assert "Keine benutzerdefinierten Konvertierungen" in response.text
