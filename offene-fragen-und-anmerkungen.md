# Offene Fragen & Anmerkungen zu den User Stories

## Story 1: Individuelle Personenanzahl pro Rezept

Keine offenen Fragen - die Anforderung ist klar. Technisch straightforward: `custom_servings` Feld auf `MealPlan`.

---

## Story 2: Kompaktere Einkaufsliste + Bemerkungszeile

**Frage: Was genau ist mit "Bemerkungszeile" gemeint?**

| Option | Beispiel | Einschätzung |
|---|---|---|
| **A: Pro Zutat** | Butter → "Bio kaufen" / Milch → "laktosefrei prüfen" | Macht am meisten Sinn beim Einkaufen. Braucht aber ein neues Feld im Datenmodell (z.B. auf `RecipeIngredient` oder `Ingredient`) |
| **B: Pro Kategorie** | Unter "Milchprodukte" → "Alles bei Rewe holen" | Nischiger Anwendungsfall |
| **C: Allgemein am Ende** | "Bis Freitag besorgen, Budget: 500€" | Am einfachsten umzusetzen, könnte ein Freitext-Feld beim Export-Dialog sein |

**Empfehlung:** Option A (pro Zutat) - eine zusätzliche Spalte "Bemerkung" in der PDF-Tabelle. Allerdings: Wo wird die Bemerkung eingegeben? Direkt in der Einkaufslisten-Ansicht wäre am intuitivsten.

---

## Story 3: Tageweise Rezept-PDF

**Frage: Wie sollen Untergruppen beim Abendessen behandelt werden (Vorspeise/Hauptgang/Salat)?**

Im Screenshot hat das Abendessen klare Untergruppen. Das Datenmodell kennt nur BREAKFAST/LUNCH/DINNER.

| Option | Umsetzung | Einschätzung |
|---|---|---|
| **A: Ignorieren** | Mehrere Rezepte pro Slot einfach nacheinander anzeigen | Funktioniert sofort, aber verliert die Struktur aus dem Screenshot |
| **B: `notes`-Feld nutzen** | MealPlan hat schon ein `notes`-Feld → dort "Vorspeise", "Hauptgang" etc. eintragen | Kein DB-Change nötig, aber etwas hacky. Das `notes`-Feld wird auch für andere Zwecke genutzt |
| **C: Neues Feld `sub_category`** | Eigenes optionales Feld auf MealPlan | Saubere Lösung, braucht DB-Migration + UI-Anpassung beim Drag&Drop |

**Empfehlung:** Option C - ein optionales `sub_category`-Feld ist sauber und zukunftssicher. Beim Drag&Drop ins Abendessen könnte ein kleines Dropdown erscheinen: "Vorspeise / Hauptgang / Beilage / Salat / Nachtisch" (oder leer lassen).

---

## Story 4: Rezept-Vorschau in Wochenübersicht

**Frage: Modal oder Popover?**

| Option | Vorteil | Nachteil |
|---|---|---|
| **A: Modal** | Viel Platz für Zutaten + Anleitung | Verdeckt den Kalender komplett |
| **B: Popover/Sidebar** | Kalender bleibt sichtbar | Weniger Platz |

**Empfehlung:** Modal - die Zutaten + Zubereitung brauchen Platz. Ein Klick auf das Rezept öffnet den Dialog, Escape/Klick-außerhalb schließt ihn. Passt gut zum bestehenden Alpine.js + HTMX Stack.

Eigentlich keine Frage, die beantwortet werden muss - eher eine Designentscheidung.

---

## Story 5: Reste-Tracker - die meisten offenen Fragen

### Frage 1: Granularität - pro Rezept oder pro Zutat?

| Option | Beispiel | Einschätzung |
|---|---|---|
| **A: Pro Rezept** | "Pizzasuppe → ca. 15 Portionen übrig" | Einfacher zu erfassen, reicht für Statistik "beim nächsten Mal weniger kochen" |
| **B: Pro Zutat** | "3kg Nudeln übrig, 2L Soße übrig" | Viel Aufwand beim Eintragen, aber nützlich wenn man Reste für andere Rezepte verwerten will |
| **C: Kombi** | Portionen-Schätzung + Freitext-Beschreibung | Guter Kompromiss |

**Empfehlung:** Option C - eine Portionszahl (für Statistik) plus ein Freitext-Feld (für Details wie "3kg Nudeln, 2L Soße"). Einfach einzutragen, trotzdem flexibel.

### Frage 2: Wann wird eingetragen?

| Option | Einschätzung |
|---|---|
| **A: Nach jeder Mahlzeit** | Genauer, aber aufwändiger im Alltag |
| **B: Am Ende des Tages** | Praktischer, aber man vergisst Details |
| **C: Flexibel, jederzeit** | Am besten - einfach einen Button "Reste erfassen" pro Mahlzeit im Kalender |

**Empfehlung:** Option C - ein Button pro geplanter Mahlzeit, den man klicken kann wann man will. Kein Zwang, kein fester Zeitpunkt.

### Frage 3: Was soll die Statistik zeigen?

Mögliche Auswertungen:
- "Pizzasuppe: In 3 von 4 Freizeiten blieben Reste (Ø 12 Portionen)"
- "Empfehlung: Nächstes Mal für 35 statt 45 Personen skalieren"
- Rezepte sortiert nach "meiste Reste" / "keine Reste"

### Frage 4: Soll die Statistik automatisch die Skalierung anpassen?

| Option | Einschätzung |
|---|---|
| **A: Nur anzeigen** | Sicherer - der User entscheidet selbst |
| **B: Vorschlag machen** | "Basierend auf Erfahrung: 38 statt 45 Portionen empfohlen" |
| **C: Automatisch anpassen** | Riskant - was wenn die Daten schlecht sind? |

**Empfehlung:** Option B - Vorschlag anzeigen, aber nicht automatisch anpassen. Der Küchenplaner weiß am besten, ob die Situation vergleichbar ist.

---

## Zusammenfassung: Rückmeldung benötigt zu

1. **Bemerkungszeile:** Pro Zutat, pro Kategorie oder allgemein?
2. **Untergruppen Abendessen:** Ignorieren, `notes` nutzen oder neues Feld?
3. **Reste - Granularität:** Pro Rezept, pro Zutat oder Kombi?
4. **Reste - Erfassung:** Nach jeder Mahlzeit, am Tagesende oder flexibel?
5. **Reste - Statistik:** Nur anzeigen, Vorschlag machen oder automatisch anpassen?
