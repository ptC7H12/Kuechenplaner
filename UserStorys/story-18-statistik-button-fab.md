# Story 18: Reste-Seite — Statistik-Button als FAB

**Status:** Done
**Aufwand:** Sehr klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/leftovers/index.html:126-136` (FAB-Container, `.fab-extended fab-extended-primary`, Chart-Icon, konsistent zu anderen Seiten)

## Beschreibung

Als Küchenplaner möchte ich, dass die "Statistik anzeigen"-Aktion als Floating Action Button (FAB) rechts unten erscheint, analog zum "Neues Rezept"- und "Excel-Export"-Button auf den anderen Seiten.

## Ist-Zustand

- "Statistik anzeigen" ist aktuell ein normaler `.btn.btn-secondary` oben rechts neben dem Header (`leftovers/index.html:15`)
- FAB-Pattern existiert in `app/static/css/custom.css:217-254` und wird in `recipes/list.html:588-610` und `shopping_list.html:288-321` genutzt
- Wiederverwendbare Komponente: `app/templates/components/fab_button.html`

## Akzeptanzkriterien

- [x] Statistik-Button erscheint als FAB rechts unten (fixed bottom-right)
- [x] Visuell konsistent mit den FAB-Buttons in `recipes/list.html` und `shopping_list.html`
- [x] Verwendet die bestehende `fab_button.html`-Komponente oder das `.fab-container`/`.fab-extended`-Pattern aus `custom.css`
- [x] Verwendet `.fab-extended-primary` oder `.fab-extended-accent` (passende Variante wählen)
- [x] Keine neuen CSS-Regeln nötig

## Technische Umsetzung

- FAB-Container am Ende von `leftovers/index.html` einfügen (analog `shopping_list.html:288-321`)
- Bestehenden Button aus dem Header entfernen (vgl. Story 17)
- Icon: Chart-/Statistik-SVG (z.B. analog zu Chart-Icons in bestehenden Templates)
