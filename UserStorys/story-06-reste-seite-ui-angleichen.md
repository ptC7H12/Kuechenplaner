# Story 6: Reste-Seite UI an restliche App angleichen

**Status:** Done
**Aufwand:** Klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/leftovers/index.html:52` (`.card` Wrapper), `app/templates/leftovers/index.html:81` (`.btn btn-icon` Löschen), `app/templates/leftovers/index.html:8-48` (Stat-Cards)

## Beschreibung

Als Küchenplaner möchte ich, dass die Reste-Seite im selben visuellen Stil daherkommt wie Rezeptübersicht und Einkaufsliste, damit sich die App konsistent anfühlt.

## Ist-Zustand

- `app/templates/leftovers/index.html` zeigt eine nackte Tabelle in `bg-white rounded-xl shadow-md border-2` (kein `.card` Wrapper, kein Header-Gradient, keine Stat-Cards)
- "Löschen"-Aktion ist als reiner Text-Link (`<button class="text-red-600 hover:text-red-800 text-sm font-medium">`) gerendert — andere Seiten nutzen durchgängig `.btn btn-icon` mit Trash-SVG
- Page-Header ist nur ein `h1`, kein Stat-Block wie bei `recipes/index.html`

## Akzeptanzkriterien

- [x] Header-Bereich nutzt das gleiche Pattern wie `recipes/index.html` (Page-Title `text-2xl font-black text-gray-900` + optional `.info-card` Stat-Cards für "Einträge gesamt", "Ø Restmenge", "Rezepte mit Resten")
- [x] Tabellen-Container nutzt die bestehende `.card`-Klasse aus `custom.css`
- [x] Löschen-Button in den Tabellenzeilen als `.btn btn-icon text-red-600` mit Trash-SVG (analog Speiseplan-Box, Rezeptliste, Einkaufsliste)
- [x] "Statistik anzeigen" bleibt `.btn btn-secondary` (bereits korrekt)
- [x] Keine neuen CSS-Regeln nötig — ausschließlich bestehende Klassen aus `custom.css`

## Technische Umsetzung

- `app/templates/leftovers/index.html` umbauen, dabei das Header- und Card-Pattern aus `app/templates/recipes/index.html` übernehmen
- Lösch-Icon-SVG aus `meal_planning/index.html` (Trash) kopieren
