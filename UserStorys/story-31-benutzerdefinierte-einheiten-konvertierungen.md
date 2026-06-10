# Story 31: Benutzerdefinierte Einheiten-Konvertierungen speichern und löschen

**Status:** Done
**Aufwand:** Klein
**Machbarkeit:** Gut
**Implementiert in:** `app/routers/settings.py:33,108,265-321`, `app/templates/settings/index.html:147-180`, `app/templates/settings/_conversions_list.html`, `tests/test_settings_units.py`

## Beschreibung

Als Küchenplaner möchte ich in den Einstellungen benutzerdefinierte Einheiten-Konvertierungen (z. B. Becher → 250 ml) eingeben, speichern und wieder löschen können, damit eigene Mengenangaben automatisch in Standard-Einheiten umgerechnet werden.

## Ist-Zustand

- `app/templates/settings/index.html:154` — Input „Von Einheit" hat kein `id`-Attribut; Wert nicht per JavaScript auslesbar.
- `app/templates/settings/index.html:157-162` — Inputs „Zu Einheit" und „Faktor" ebenfalls ohne `id`; kein Schwellenwert-Feld (wird intern nicht benötigt, da immer `threshold=1`).
- `app/templates/settings/index.html:165-170` — „Hinzufügen"-Button hat weder `hx-*`-Attribute noch `onclick`-Handler; Klick löst nichts aus.
- `app/templates/settings/index.html:174-176` — Liste gespeicherter Konvertierungen ist statischer Platzhalter-Text; wird nie aus der DB geladen.
- `app/routers/settings.py:258-262` — `POST /settings/api/settings/units/conversions` existiert für Bulk-Update; kein Einzel-Konvertierung-Add- oder -Delete-Endpoint vorhanden.
- `app/services/unit_converter.py:99-114` — `add_custom_conversion` und `remove_custom_conversion` sind fertig implementiert, werden aber von keinem Endpoint aufgerufen.

## Akzeptanzkriterien

- [x] Formular-Inputs für „Von Einheit", „Zu Einheit" und „Faktor" haben `id`-Attribute; Werte sind über HTMX auslesbar.
- [x] Klick auf „Hinzufügen" sendet die neue Konvertierung an den Backend-Endpoint; Erfolg wird per Toast bestätigt.
- [x] Nach dem Speichern erscheint die neue Konvertierung sofort in der Liste (HTMX-Partial-Update, kein Full-Reload).
- [x] Jede gespeicherte Konvertierung hat einen „Löschen"-Button, der sie einzeln aus der DB entfernt.
- [x] Beim Laden der Einstellungsseite werden bestehende Konvertierungen aus der DB geladen und angezeigt.
- [x] Threshold wird intern immer auf `1` gesetzt; kein entsprechendes Eingabefeld im Formular.
- [x] Validierung: alle drei Felder müssen ausgefüllt sein; Faktor muss eine positive Zahl sein.
- [x] Pytest deckt ab: Konvertierung hinzufügen, auflisten und löschen über die neuen Endpoints.

## Technische Umsetzung (Vorschlag)

### Backend

- `app/routers/settings.py`:
  - Neuer Endpoint `POST /api/settings/units/conversions/add` — erwartet Form-Parameter `from_unit`, `to_unit`, `factor`; ruft `unit_converter.add_custom_conversion(db, from_unit, to_unit, threshold=1, factor=float(factor))` auf; gibt HTMX-Partial `_conversions_list.html` zurück.
  - Neuer Endpoint `DELETE /api/settings/units/conversions/{from_unit}` — ruft `unit_converter.remove_custom_conversion(db, from_unit)` auf; gibt aktualisiertes HTMX-Partial zurück.
  - Settings-Seitenroute (`GET /settings`): `unit_conversions = unit_converter.load_custom_conversions(db)` laden und in Template-Context übergeben.

### Frontend

- `app/templates/settings/index.html:147-178`:
  - Inputs IDs vergeben: `id="conv-from"`, `id="conv-to"`, `id="conv-factor"`.
  - Formular-Wrapper `<form hx-post="/settings/api/settings/units/conversions/add" hx-target="#conversions-list" hx-swap="innerHTML">` um die drei Inputs + Button.
  - Container `<div id="conversions-list">` um die Konvertierungsliste setzen.
  - Initiales Rendern der Liste aus dem Template-Context (Loop über `unit_conversions`).
- Neues Partial-Template `app/templates/settings/_conversions_list.html`:
  - Loop über übergebene Konvertierungen; jede Zeile mit `hx-delete` und `hx-target="#conversions-list"`.
  - Fallback-Text, wenn Liste leer ist.

### Tests

- `tests/test_settings_units.py` (neu): je ein Test für Add-Endpoint (200, Eintrag in DB), Delete-Endpoint (200, Eintrag entfernt) und leere Initialliste.
