# Story 17: Reste-Seite Header reduzieren

**Status:** Done
**Aufwand:** Sehr klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/leftovers/index.html:8-48` (großer Title-Block entfernt, nur Stat-Dashboard), `app/templates/leftovers/index.html:126` (FAB am Ende)

## Beschreibung

Als Küchenplaner möchte ich, dass die Reste-Seite den gleichen kompakten Header-Stil hat wie die anderen Listenseiten (Rezepte, Einkaufsliste), damit die App konsistent wirkt und mehr Platz für Inhalte bleibt.

## Ist-Zustand

- `app/templates/leftovers/index.html:8-16` zeigt einen großen Title-Block ("Reste-Erfassung" mit Untertitel + Statistik-Button rechts)
- Daneben Stats-Dashboard mit 3 Gradient-Cards (`:19-60`)
- Andere Seiten (`recipes/list.html`, `shopping_list.html`) haben nur einen schlichten Page-Title

## Akzeptanzkriterien

- [x] Der große Title-Block ("Reste-Erfassung" Header inkl. Beschreibungstext) wird entfernt — der Tab-Name im Browser reicht (analog zu anderen Seiten)
- [x] Das Stats-Dashboard (3 Cards) bleibt erhalten — verschiebt nach oben oder bleibt direkt nach Header-Bereich
- [x] Vergleich zu `recipes/list.html` und `shopping_list.html` zeigt einheitliches Layout

## Technische Umsetzung

- `app/templates/leftovers/index.html:8-16` entfernen
- Statistik-Button wandert in den FAB-Container (siehe Story 18) — daher hier komplett entfernen
- Stats-Dashboard rückt nach oben
