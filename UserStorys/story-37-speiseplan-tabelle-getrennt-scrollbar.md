# Story 37: Speiseplan-Tabelle getrennt scrollbar

**Status:** Done
**Aufwand:** Sehr klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/meal_planning/index.html:100` (rechter Tabellen-Container `lg:max-h-[600px] lg:overflow-y-auto`, `overflow-x-auto` beibehalten; auf Mobil ohne Höhenbegrenzung)

## Beschreibung

Als Küchenplaner möchte ich, dass die Plan-Tabelle rechts unabhängig von der Rezept-Suche links scrollt, damit beim Scrollen im Plan nach unten die Rezeptliste links weiterhin sichtbar bleibt.

## Ist-Zustand

- `app/templates/meal_planning/index.html:18` — Zwei-Spalten-Grid (`grid grid-cols-1 lg:grid-cols-4 gap-6`).
- `app/templates/meal_planning/index.html:20-21` — linke Sidebar (`col-span-1`) bereits `sticky top-4`.
- `app/templates/meal_planning/index.html:39` — Rezept-Sidebar mit `max-h-[600px] overflow-y-auto` (eigenständig scrollbar).
- `app/templates/meal_planning/index.html:100` — rechte Plan-Tabelle (`col-span-3`) nur `overflow-x-auto`; vertikal scrollt der gesamte Seiteninhalt mit.
- `app/templates/meal_planning/index.html:110,146` — Sticky-Datumsspalte (`sticky left-0`) im horizontalen Scroll.

## Akzeptanzkriterien

- [x] Die rechte Plan-Tabelle ist vertikal eigenständig scrollbar (eigener `max-h` + `overflow-y-auto`), ohne dass die linke Sidebar mitscrollt.
- [x] Beim Runterscrollen im Plan bleibt die Rezept-Suche links im Blick.
- [x] Drag-and-Drop (SortableJS) und die Sticky-Datumsspalte (`sticky left-0`) bleiben funktionsfähig.
- [x] In der mobilen, einspaltigen Ansicht bleibt das Verhalten brauchbar (kein abgeschnittener Inhalt, kein doppelter Scrollbalken).

## Technische Umsetzung (Vorschlag)

### Frontend

- `app/templates/meal_planning/index.html` — die rechte Spalte (`:98-100`) in einen vertikal scrollbaren Container wrappen (`max-h-[…] overflow-y-auto`), Höhe konsistent zur Sidebar (`max-h-[600px]`); `overflow-x-auto` für die horizontale Tabellen-Scrollbarkeit beibehalten.
- Auf Mobil (`grid-cols-1`) die `max-h`/`overflow-y`-Begrenzung zurücknehmen (z. B. nur `lg:`-Präfix), damit der Plan dort normal in der Seite scrollt.
- Sicherstellen, dass `sticky left-0` und SortableJS innerhalb des neuen Scroll-Containers weiter korrekt funktionieren.
