# Story 19: Reste-Seite — Löschen-Button-Bug beheben

**Status:** Done
**Aufwand:** Sehr klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/leftovers/index.html:108-122` (`deleteLeftover()` Funktion mit fetch DELETE + showToast + reload), `app/templates/leftovers/index.html:80` (Button verkabelt)

## Beschreibung

Als Küchenplaner möchte ich, dass der Löschen-Button in der Reste-Tabelle einen Eintrag tatsächlich entfernt — aktuell passiert nichts beim Klick.

## Ist-Zustand

- Löschen-Icon in `app/templates/leftovers/index.html:93-94` verkabelt mit Inline-JS
- JS-Funktion in `leftovers/index.html:119-124` ruft `window.FreizeitApp.deleteLeftover(id)` → DELETE `/leftovers/api/leftovers/{id}`
- Backend-Endpunkt existiert: `app/routers/leftovers.py:149-154`
- User-Report: Klick auf den Button hat keine Wirkung — Eintrag bleibt in der Liste

## Akzeptanzkriterien

- [x] Klick auf das Löschen-Icon zeigt Confirm-Dialog
- [x] Nach Bestätigung wird DELETE-Request gesendet
- [x] Bei Erfolg verschwindet die Zeile aus der Tabelle (entweder durch Reload, HTMX-Swap oder Alpine-State-Update)
- [x] Toast-Notification "Eintrag gelöscht" wird angezeigt
- [x] Bei Fehler: Error-Toast mit verständlicher Meldung

## Technische Umsetzung

- Investigation nötig: Wird `window.FreizeitApp.deleteLeftover` überhaupt definiert? Prüfen in `app/templates/base.html` und ggf. globalen JS-Files
- Wenn Funktion fehlt: implementieren analog zu anderen `delete*`-Helpern in `base.html`
- Wenn Funktion vorhanden, aber DELETE-Response nicht im UI reflektiert wird: Page-Reload oder `outerHTML`-Swap der `<tr>` nach Success
- Endpunkt-URL prüfen: Template nutzt `/leftovers/api/leftovers/{id}` — sicherstellen, dass das mit dem Router-Prefix in `leftovers.py` übereinstimmt
