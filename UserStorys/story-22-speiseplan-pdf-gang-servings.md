# Story 22: Speiseplan-PDF — Gang und Custom-Servings anzeigen

**Status:** Done
**Aufwand:** Sehr klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/routers/export.py:402-404` (Inline-Rendering: `prefix = f"{mp.sub_category}: "`, `suffix = f" ({mp.custom_servings} Pers.)"`, beide im Zelltext)

## Beschreibung

Als Küchenplaner möchte ich im PDF-Export des Wochenplans (Speiseplan-PDF) sehen, ob ein Rezept einer Sub-Kategorie zugeordnet ist und ob es eine abweichende Personenanzahl hat, damit das PDF die volle Planungsinfo enthält.

## Ist-Zustand

- `app/routers/export.py:310-431` `export_meal_plan_pdf()` rendert eine Landschaft-Tabelle (Datum × Mahlzeit) und zeigt **nur** den Rezeptnamen pro Zelle (~Zeile 389)
- `sub_category` und `custom_servings` werden ignoriert
- Anders als Tageslisten-PDF und Rezeptbuch-PDF, die `custom_servings` bzw. `sub_category` bereits berücksichtigen

## Akzeptanzkriterien

- [x] Wenn `custom_servings` gesetzt ist, wird sie hinter oder unter dem Rezeptnamen angezeigt (z.B. "Creps (20 Pers.)")
- [x] Wenn `sub_category` gesetzt ist, wird sie kompakt angezeigt (z.B. "Vorspeise: Nachos")
- [x] Mehrere Rezepte einer Mahlzeit (z.B. Vorspeise + Hauptgang) werden in einer Zelle untereinander mit jeweils ihrer Sub-Category dargestellt
- [x] Layout bleibt lesbar — Zellen werden nicht übermäßig hoch
- [x] Stilistisch konsistent zur bestehenden Tabellen-Darstellung

## Technische Umsetzung

- In `app/routers/export.py:310-431` den Cell-Renderer (~Zeile 389) erweitern
- Format-Helper: `format_meal_cell(meal_plans) -> str` baut den Zelltext aus 1..n Rezepten zusammen
- Falls vorhanden: Custom-Servings als kleine `Paragraph` im Stil eines Badge in Klammern hinter dem Namen
- Falls vorhanden: Sub-Category als Präfix vor dem Rezeptnamen mit Doppelpunkt (z.B. "Vorspeise: Nachos")
