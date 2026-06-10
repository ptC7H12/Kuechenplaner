# Story 34: Rezeptliste — Name + Tags/Allergene zweizeilig (auch mobil)

**Status:** Done
**Aufwand:** Klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/recipes/list.html:288-323` (Namens-Zelle mit zweizeiliger Tag-/Allergen-Info), `app/templates/recipes/list.html:266` (Tags-Header entfernt), `app/templates/recipes/list.html:345` (separate Tags-Spalte entfernt)

## Beschreibung

Als Küchenplaner möchte ich in der Rezeptliste neben dem großen Symbol zweizeilige Informationen sehen — oben den Rezeptnamen, darunter Tags und Allergene —, damit ich diese Angaben auch in der mobilen Ansicht sehe (aktuell ist dort nur der Name sichtbar).

## Ist-Zustand

- `app/templates/recipes/list.html:288-297` — großes Symbol/Bild (12×12) vor dem Rezeptnamen.
- `app/templates/recipes/list.html:300` — Rezeptname einzeilig (`text-sm font-bold`).
- `app/templates/recipes/list.html:301-312` — Allergen-Icons aktuell als separate Zeile/Vorschau unter dem Namen.
- `app/templates/recipes/list.html:346-363` — Tags in einer **eigenen Spalte** mit `hidden lg:table-cell` (auf Mobil und Tablet ausgeblendet); zeigt 2 Tags + „+N".
- Tag-Badge-Stil: `background-color: {{ tag.color }}20; color: {{ tag.color }}; border-color: …` (siehe `_form.html:398`).

## Akzeptanzkriterien

- [x] In der Namens-Zelle steht der Rezeptname oben; direkt darunter eine zweite Zeile mit Tag-Badges **und** Allergen-Badges.
- [x] Diese Info-Zeile ist auf allen Breakpoints sichtbar (kein `hidden`-Ausblenden auf Mobil/Tablet).
- [x] Die bisherige separate Tags-Spalte wird entfernt oder nur noch als zusätzliche reine Desktop-Spalte beibehalten — keine doppelte oder widersprüchliche Darstellung.
- [x] Badge-Stil konsistent mit den bestehenden Tag-Badges (Farbe aus `tag.color`); Allergene werden mit Icon dargestellt.
- [x] Lange Tag-/Allergen-Listen brechen sauber um (`flex-wrap`) bzw. werden auf X sichtbare + „+N" begrenzt, damit die Zeile nicht überläuft.

## Technische Umsetzung (Vorschlag)

### Frontend

- `app/templates/recipes/list.html` — Namens-Zelle (`:288-312`) umbauen:
  - Die Text-Spalte neben dem Symbol als vertikaler Flex-Container (`flex flex-col`): Zeile 1 = Rezeptname, Zeile 2 = `flex flex-wrap gap-1` mit Tag-Badges (aus `recipe.tags`) und Allergen-Badges (aus `recipe.allergens`).
  - Begrenzung analog der bestehenden Tags-Spalte (2-3 sichtbare Badges + „+N").
- Die separate Tags-Spalte (`:346-363`) sowie deren Header (`:266`) entfernen oder auf reine Desktop-Zusatzinfo reduzieren.
- Keine Backend-Änderung nötig — `recipe.tags` und `recipe.allergens` stehen im Context bereits zur Verfügung.

### Tests

- Optional/leichtgewichtig: kein zwingender Pytest (reine Template-/Darstellungsänderung). Bei Bedarf Smoke-Test, dass die Rezeptliste rendert und Tag-/Allergen-Namen im HTML enthalten sind.
