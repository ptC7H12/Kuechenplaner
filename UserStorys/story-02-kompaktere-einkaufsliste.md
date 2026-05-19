# Story 2: Kompaktere Einkaufsliste-PDF + Bemerkungszeile

**Status:** Done
**Aufwand:** Klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/models.py` (`ShoppingListNote`, Zeilen 94-106), `alembic/versions/003_shopping_notes.py`, `app/templates/shopping_list.html:157` (textarea), `app/crud.py` (UPSERT-Funktion), `tests/test_shopping_notes.py`, `app/routers/export.py` (`export_shopping_list_pdf`)

## Beschreibung

Als Küchenplaner möchte ich eine kompaktere Einkaufsliste als PDF exportieren können und eine Möglichkeit haben, Bemerkungen hinzuzufügen, damit die Liste praktischer beim Einkaufen ist.

## Ist-Zustand

- Großzügige Abstände: 2cm Ränder, `Spacer(1, 20)` zwischen Kategorien
- Schriftgrößen: Titel 24pt, Überschriften 16pt
- Keine Möglichkeit für Bemerkungen
- Tabelle: 3 Spalten (Zutat, Menge, Einheit) - relativ breit

## Akzeptanzkriterien

- [x] PDF-Ränder reduziert (z.B. 1.5cm statt 2cm)
- [x] Abstände zwischen Kategorien verringert
- [x] Schriftgrößen etwas kleiner (Titel 18pt, Überschriften 13pt)
- [x] Tabellenzeilen kompakter (weniger Padding)
- [x] Zusätzliche Spalte "Bemerkung" pro Zutat in der PDF-Tabelle
- [x] Eingabefeld für Bemerkungen pro Zutat in der Einkaufslisten-Ansicht
- [x] Die Liste passt auf weniger Seiten als vorher

## Technische Umsetzung

- `export.py` → `export_shopping_list_pdf()` anpassen:
  - Margins reduzieren
  - Spacer verkleinern
  - Font-Sizes reduzieren
  - TableStyle: Padding reduzieren
- Neue Spalte "Bemerkung" in der Zutat-Tabelle
- Neues Feld `note` auf dem Einkaufslisten-Eintrag (oder `ShoppingListItem`) für Bemerkungen pro Zutat
- UI: Editierbares Textfeld in der Einkaufslisten-Ansicht pro Zutat
