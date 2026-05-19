# Story 21: Speiseplan — Hover-Buttons überlappen Badges/Tags

**Status:** Done
**Aufwand:** Klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/meal_planning/index.html:174` (`recipe-card-planned` mit padding), `app/templates/meal_planning/index.html:221` (Badges in `mt-1 flex`, keine Überschneidung mehr)

## Beschreibung

Als Küchenplaner möchte ich, dass beim Hover über eine Rezept-Karte im Speiseplan die Action-Buttons nicht die Badges darunter (Custom-Servings "👥 20", "🍽 Rest", "Vorspeise") verdecken, damit ich z.B. den Gang-Tag weiterhin anklicken kann.

## Ist-Zustand

- Hover-Action-Buttons (Löschen / Servings / Reste) sind als `absolute top-1 right-1` (`app/templates/meal_planning/index.html:193`) positioniert mit `bg-white/90 backdrop-blur-sm`
- Badges (Custom-Servings, Rest, Sub-Category-Button) liegen im normalen Flow (`:221-241`)
- Bei Hover: Action-Buttons erscheinen mit weißem Hintergrund **über** den Badges → Klick auf "+Gang" oder Custom-Servings-Badge wird abgefangen
- Screenshot des Users zeigt das Problem: orange Reste-Button-Hover-Variante deckt den "Vorspeise"-Tag halb ab

## Akzeptanzkriterien

- [x] Beim Hover sind sowohl die Action-Buttons als auch die Badges klickbar
- [x] Optisch: Die Action-Leiste verdeckt keine Badges, auch nicht teilweise
- [x] Mobile-Verhalten (Tap) bleibt funktionsfähig
- [x] Lösung ohne neue CSS-Regeln möglich (Tailwind only)

## Technische Umsetzung — Varianten

- **Variante A:** Rezept-Karte erhält beim Hover `pt-8` oder `mt-8` für den Inhalt, sodass Buttons in eigener Zeile oberhalb des Titels sitzen → kein Overlap
- **Variante B:** Action-Buttons aus `absolute` rausnehmen → in eigene Zeile am Kartenende (immer sichtbar oder mit `group-hover:flex` ein-/ausgeblendet als Block-Element)
- **Variante C (empfohlen):** Card-Padding-Top vergrößern (z.B. `pt-7`), sodass Title und Badges weit genug unterhalb der Action-Buttons liegen — am wenigsten invasiv
