# Story 8: Reste-Statistik auf Rezept-Detailseite anzeigen

**Status:** Done
**Aufwand:** Klein-Mittel
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/recipes/detail.html:185-276` (Sektion "Reste-Historie"), `app/routers/recipes.py:128-129` (`get_recipe_statistics()` aufgerufen), Per-Rezept & Per-Zutat Tabelle, Vorschlag-Badge

## Beschreibung

Als Küchenplaner möchte ich auf der Rezept-Detailseite sehen, ob und wie viel von diesem Rezept in vergangenen Camps übrig geblieben ist (pro Rezept und pro Zutat), damit ich besser planen kann.

## Ist-Zustand

- `app/templates/recipes/detail.html` zeigt Hero, Metadaten, Zutaten, Zubereitung — aber keine Reste-Historie
- `app/services/leftover_statistics.py` existiert bereits und liefert Statistik-Daten — wird aber nur unter `/leftovers/statistics` verwendet

## Akzeptanzkriterien

- [x] Neue Sektion "Reste-Historie" auf der Rezept-Detailseite (einklappbar via Alpine.js `x-show`)
- [x] Pro Rezept: Anzahl Erfassungen, Ø Restmenge in %, Vorschlag "Nächstes Mal für X statt Y Personen skalieren"
- [x] Pro Zutat: Tabelle mit Spalten `Zutat | Ø Restmenge | Anzahl Camps mit Resten`
- [x] Wenn keine Daten vorhanden: dezenter Hinweis "Noch keine Reste für dieses Rezept erfasst"
- [x] Styling wie restliche Sektionen auf `recipes/detail.html` (bestehende `.card`-Klassen)

## Technische Umsetzung

- `app/services/leftover_statistics.py` wiederverwenden (kein neuer Service)
- Im `recipes`-Router den Rezept-Detail-Endpunkt erweitern: Statistik-Daten für das Rezept abrufen und ans Template übergeben
- Template-Sektion in `app/templates/recipes/detail.html` ergänzen — gleicher Card-Stil wie bestehende Zutaten/Zubereitung-Boxen
