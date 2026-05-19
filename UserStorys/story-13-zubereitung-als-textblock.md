# Story 13: Zubereitung in Tagesliste als Textblock (ohne Nummerierung)

**Status:** Done
**Aufwand:** Sehr klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/routers/export.py:635-637` (instructions_text als einzelner Paragraph, keine `split_instructions()` mehr), `app/routers/export.py:683` (SPAN für rowspan), Nummerierung entfernt

## Beschreibung

Als Küchenplaner möchte ich die Zubereitung in der Tagesliste-PDF als zusammenhängenden Text sehen, nicht zeilenweise in eine Tabellenspalte aufgeteilt und nummeriert.

## Ist-Zustand

- `app/routers/export.py:605-649` in `build_recipe_block()`:
  - `split_instructions()` splittet `recipe.instructions` per `splitlines()` und stripped Leerzeichen
  - In der PDF-Tabelle wird jeder "Schritt" in eine eigene Zeile geschrieben und mit `f"{i+1}. ..."` nummeriert
  - Resultat: künstliche Nummerierung, Layout-Brüche, schwer lesbar bei längeren Anleitungen

## Akzeptanzkriterien

- [x] Zubereitung erscheint als einzelner zusammenhängender Textblock in der Zubereitungs-Spalte
- [x] Keine künstliche `1.`, `2.`, `3.`-Nummerierung mehr (falls der Autor selbst Nummern im Text hat, bleiben die natürlich erhalten)
- [x] Zubereitungs-Zelle spannt vertikal über alle Zutaten-Zeilen (rowspan)
- [x] Falls Rezept keine Zubereitung hat: weiterhin 2-Spalten-Tabelle (Menge | Zutat) wie bisher
- [x] Recipe-Book-PDF (separater Endpunkt) bleibt unverändert oder bekommt analoge Behandlung

## Technische Umsetzung

- `split_instructions()` in `app/routers/export.py:605-608` entfernen
- `build_recipe_block()` umbauen: Zubereitungs-Zelle erhält die volle `recipe.instructions` als einzelner `Paragraph`
- ReportLab `TableStyle` mit `SPAN`-Befehl: `('SPAN', (2, 1), (2, len(ingredients)))` lässt die Zubereitungs-Spalte über alle Zutaten-Zeilen reichen
- Fallback ohne Zubereitung wie bisher: 2-Spalten-Tabelle
