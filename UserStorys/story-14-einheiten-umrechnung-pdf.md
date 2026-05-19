# Story 14: Einheiten-Umrechnung in Rezeptbuch- und Tagesliste-PDF

**Status:** Done
**Aufwand:** Sehr klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/routers/export.py:525` (`format_quantity_with_conversion()` im Rezeptbuch), `app/routers/export.py:643` (Tagesliste), `app/services/unit_converter.py` (nutzbar)

## Beschreibung

Als Küchenplaner möchte ich beim PDF-Export keine Mengen wie `35000 ml` oder `2500 g` mehr sehen, sondern automatisch umgerechnete Werte (`35 L`, `2,5 kg`), so wie es in der Einkaufsliste bereits funktioniert.

## Ist-Zustand

- `app/services/unit_converter.py` enthält `convert_unit()` mit Schwellen `1000g → kg`, `1000ml → L`, `1000mg → g`
- Diese Funktion wird ausschließlich in `app/services/calculation.py:78` für die Einkaufsliste aufgerufen
- Im Rezeptbuch-Export (`export.py:505-511`) und Tagesliste-Export (`export.py:628-629`) werden Mengen roh mit `f"{qty:.1f} {ri.unit}"` formatiert — keine Umrechnung

## Akzeptanzkriterien

- [x] Im Rezeptbuch-PDF werden Mengen automatisch in die sinnvollere Einheit umgerechnet (1500g → 1,5 kg, 2000ml → 2 L)
- [x] Im Tagesliste-PDF dasselbe Verhalten
- [x] Die Einkaufsliste-Logik bleibt unverändert (gleicher Service)
- [x] Format: Komma als Dezimaltrenner (deutsche Konvention), eine Nachkommastelle, sinnvoll gerundet

## Technische Umsetzung

- In `export.py:505-511` und `export.py:628-629` den bestehenden `convert_unit()` aus `app/services/unit_converter.py` aufrufen
- Optional: kleine Format-Helper-Funktion direkt in `unit_converter.py` ergänzen (`format_quantity(value, unit) -> str`), die Komma statt Punkt nutzt
- Beide Export-Funktionen verwenden den gleichen Helper
