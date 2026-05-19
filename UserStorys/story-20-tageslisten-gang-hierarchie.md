# Story 20: Tageslisten-PDF — Gänge hierarchisch farbig + eingerückt

**Status:** Done
**Aufwand:** Klein-Mittel
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/routers/export.py:689-717` (`build_sub_category_block()`), `app/routers/export.py:34-40` (Farbpalette), LINEBEFORE für Farbbalken, Einrückung (wrapper Table), Sortier-Logik

## Beschreibung

Als Küchenplaner möchte ich in der Tageslisten-PDF erkennen, dass mehrere Rezepte einer Mahlzeit zusammengehören (z.B. Vorspeise + Hauptgang + Nachtisch beim Abendessen), durch leichte Einrückung und dezente Farbcodierung der Sub-Kategorien.

## Ist-Zustand

- Sub-Kategorie wird nur als Text-Präfix im Rezepttitel mitgegeben (`app/routers/export.py:684-685`), z.B. "Abendessen · Vorspeise · Nachos"
- Keine visuelle Hierarchie — alle Rezepte einer Mahlzeit stehen optisch gleichberechtigt
- Aus Story 3-Referenz: Wunsch-Layout zeigt Vorspeise / Hauptgang / Salat eingerückt unter "Abendbrot"

## Designentscheidung (geklärt: Farbig + Einrückung)

- Mahlzeit-Überschrift bleibt linksbündig (z.B. "Abendessen")
- Pro Gang darunter: ~1cm Einrückung + linker Farbbalken (~3mm) in Gang-Farbe
- Farbpalette pro Sub-Category:
  - Vorspeise → Grün (`#10b981`)
  - Hauptgang → Indigo/Lila (`#6366f1`)
  - Beilage → Gelb-Ocker (`#d97706`)
  - Salat → Hellgrün (`#84cc16`)
  - Nachtisch → Orange (`#f97316`)
  - Ohne Sub-Category: Grau (`#6b7280`)
- Wenn nur ein Rezept ohne Gang in der Mahlzeit: keine Einrückung, kein Farbbalken (bestehendes Layout)

## Akzeptanzkriterien

- [x] Tageslisten-PDF gruppiert Rezepte einer Mahlzeit unter eine gemeinsame Mahlzeit-Überschrift
- [x] Rezepte mit gesetzter `sub_category` werden ~1cm eingerückt mit linkem Farbbalken
- [x] Gang-Name (z.B. "Vorspeise") erscheint als Sub-Überschrift in der jeweiligen Farbe
- [x] Reihenfolge der Gänge: Vorspeise → Hauptgang → Beilage → Salat → Nachtisch (siehe Reihenfolge in `app/constants.py:9`)
- [x] Rezepte ohne `sub_category` werden unsortiert vor/nach den gesetzten Gängen platziert (Entscheidung im Implementierungs-Schritt)
- [x] Mahlzeiten mit nur einem Rezept ohne Gang behalten das bestehende Layout (keine Einrückung)
- [x] PDF bleibt druckerfreundlich (Farben dezent, nicht zu kräftig)

## Technische Umsetzung

- `app/routers/export.py:528-697` `export_daily_lists_pdf()` und Helper `build_recipe_block()` erweitern
- Farbmapping als Modul-Konstante: `SUB_CATEGORY_COLORS = {"Vorspeise": colors.HexColor("#10b981"), ...}`
- Sortier-Logik für Rezepte innerhalb einer Mahlzeit: nach Sub-Category in fester Reihenfolge
- ReportLab: linker Rand des Recipe-Blocks via `Indenter` oder Tabellen-Wrapper. Farbbalken via `TableStyle('LINEBEFORE', (0,0), (0,-1), 2, color)`
- Mahlzeit-Überschrift bleibt einmalig pro Mahlzeit (nicht mehr "Abendessen · Vorspeise · Rezeptname" → nur "Abendessen", darunter "Vorspeise: Rezeptname" eingerückt)
