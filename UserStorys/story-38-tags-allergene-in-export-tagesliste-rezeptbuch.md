# Story 38: Tags/Allergene in Tagesliste- und Rezeptbuch-Export

**Status:** Done
**Aufwand:** Klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/routers/export.py:505-513` (Rezeptbuch: Tags-Paragraph vor Allergenen), `app/routers/export.py:612-632` (Tagesliste `build_recipe_block`: Tag-/Allergen-Zeile, gibt Flowable-Liste zurück), `app/routers/export.py:692-700,754` (angepasste Call-Sites), `tests/test_export_daily_lists.py` (3 neue Tests + PDF-Text-Decoder)

## Beschreibung

Als Küchenplaner möchte ich, dass beim Export der Tagesliste und des Rezeptbuchs auch Tags und Allergene ausgegeben werden, damit diese Informationen in den ausgedruckten Listen sichtbar sind.

## Ist-Zustand

- `app/routers/export.py:536-678` — `export_daily_lists_pdf` / `build_recipe_block`: gibt weder Tags noch Allergene aus (Tabellenkopf nur `["Menge", "Zutat"]`).
- `app/routers/export.py:443-533` — `export_recipe_book_pdf` (Camp-Rezeptbuch); `:505-508` rendert Allergene, **Tags fehlen**.
- `app/routers/export.py:870-877` — `export_all_recipes_pdf` rendert Tags **und** Allergene bereits (`<b>Tags:</b> …`, `<b>Allergene:</b> …`) → Muster zum Wiederverwenden.
- `app/routers/export.py:14-19` — PDF-Erzeugung via ReportLab (`SimpleDocTemplate`, `Table`, `Paragraph`).

## Akzeptanzkriterien

- [x] Die Tagesliste-PDF (Tages-Kochbuch) zeigt pro Rezept Tags und Allergene.
- [x] Die Rezeptbuch-PDF (Camp) zeigt zusätzlich Tags (Allergene bleiben wie bisher).
- [x] Die Darstellung ist konsistent zum bestehenden Muster in `export_all_recipes_pdf` (`Tags:` / `Allergene:` als Paragraph).
- [x] Rezepte ohne Tags bzw. ohne Allergene erzeugen keine leeren oder fehlerhaften Zeilen.
- [x] Pytest deckt ab: Tagesliste- und Rezeptbuch-Export rendern Tags + Allergene (Smoke-Test auf Inhalt / kein Fehler bei fehlenden Werten).

## Technische Umsetzung (Vorschlag)

### Backend

- `app/routers/export.py` — `build_recipe_block` (`:612-678`) im Tagesliste-Export um Tag- und Allergen-Paragraphen ergänzen (analog `export_all_recipes_pdf:870-877`), jeweils nur rendern, wenn vorhanden.
- `export_recipe_book_pdf` (`:443-533`) um einen Tags-Paragraphen erweitern, direkt beim bestehenden Allergen-Block (`:505-508`).
- Bestehende Helfer/Stilvorlagen aus `export_all_recipes_pdf` wiederverwenden statt neu zu definieren.

### Tests

- `tests/test_export_daily_lists.py` — erweitern: Export enthält Tag- und Allergen-Namen; Rezept ohne Tags/Allergene erzeugt keinen Fehler.
- Falls vorhanden, Rezeptbuch-Export-Test analog um Tags-Prüfung ergänzen.
