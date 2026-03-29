# User Stories - Neue Anforderungen

## Status

> Alle offenen Fragen sind geklaert (Stand: 29.03.2026). Details siehe `offene-fragen-und-anmerkungen.md`.

---

## Story 1: Individuelle Personenanzahl pro Rezept im Mahlzeitenplan

**Aufwand:** Mittel | **Machbarkeit:** Gut

### Beschreibung
Als Küchenplaner möchte ich für einzelne Rezepte im Mahlzeitenplan eine abweichende Personenanzahl angeben können, damit ich flexibel planen kann, wenn z.B. beim Frühstück weniger Leute essen als beim Mittagessen.

### Ist-Zustand
- `participant_count` liegt auf dem **Camp** (global für alle Mahlzeiten)
- Skalierung: `camp.participant_count / recipe.base_servings`
- Kein Override pro MealPlan-Eintrag möglich

### Akzeptanzkriterien
- [ ] Jeder MealPlan-Eintrag hat ein optionales Feld `custom_servings`
- [ ] Wenn `custom_servings` gesetzt ist, wird dieses statt `camp.participant_count` für die Skalierung verwendet
- [ ] In der Wochenübersicht ist die abweichende Personenanzahl sichtbar (z.B. kleiner Badge)
- [ ] Beim Drag & Drop eines Rezepts kann optional eine Personenanzahl eingegeben werden
- [ ] Die Einkaufsliste berücksichtigt die individuellen Personenanzahlen korrekt
- [ ] Der PDF-Export (Rezeptbuch) zeigt die korrekte Personenanzahl pro Rezept

### Technische Umsetzung
- `MealPlan.custom_servings` (Integer, nullable) in `models.py` hinzufügen
- `calculation.py` → `calculate_shopping_list()` anpassen: `custom_servings or camp.participant_count`
- UI: Kleines Eingabefeld oder Popup beim Platzieren/Bearbeiten eines Rezepts
- Alle Export-Funktionen in `export.py` anpassen

### Hinweise
- Standardverhalten bleibt: Ohne Override gilt weiterhin `camp.participant_count`
- DB-Migration nötig (neues Feld in `meal_plans` Tabelle)

---

## Story 2: Kompaktere Einkaufsliste-PDF + Bemerkungszeile

**Aufwand:** Klein | **Machbarkeit:** Sehr gut

### Beschreibung
Als Küchenplaner möchte ich eine kompaktere Einkaufsliste als PDF exportieren können und eine Möglichkeit haben, Bemerkungen hinzuzufügen, damit die Liste praktischer beim Einkaufen ist.

### Ist-Zustand
- Großzügige Abstände: 2cm Ränder, `Spacer(1, 20)` zwischen Kategorien
- Schriftgrößen: Titel 24pt, Überschriften 16pt
- Keine Möglichkeit für Bemerkungen
- Tabelle: 3 Spalten (Zutat, Menge, Einheit) - relativ breit

### Akzeptanzkriterien
- [ ] PDF-Ränder reduziert (z.B. 1.5cm statt 2cm)
- [ ] Abstände zwischen Kategorien verringert
- [ ] Schriftgrößen etwas kleiner (Titel 18pt, Überschriften 13pt)
- [ ] Tabellenzeilen kompakter (weniger Padding)
- [ ] Zusaetzliche Spalte "Bemerkung" pro Zutat in der PDF-Tabelle
- [ ] Eingabefeld fuer Bemerkungen pro Zutat in der Einkaufslisten-Ansicht
- [ ] Die Liste passt auf weniger Seiten als vorher

### Technische Umsetzung
- `export.py` → `export_shopping_list_pdf()` anpassen:
  - Margins reduzieren
  - Spacer verkleinern
  - Font-Sizes reduzieren
  - TableStyle: Padding reduzieren
- Neue Spalte "Bemerkung" in der Zutat-Tabelle
- Neues Feld `note` auf dem Einkaufslisten-Eintrag (oder `ShoppingListItem`) fuer Bemerkungen pro Zutat
- UI: Editierbares Textfeld in der Einkaufslisten-Ansicht pro Zutat

---

## Story 3: Tageweise Rezept-PDF (Tages-Kochbuch)

**Aufwand:** Mittel | **Machbarkeit:** Gut

### Beschreibung
Als Küchenplaner möchte ich eine PDF exportieren können, in der die Rezepte tageweise gruppiert dargestellt werden (wie die "Tageslisten" in der bisherigen Excel-Planung), damit ich am jeweiligen Tag schnell sehe, was gekocht wird, welche Zutaten ich brauche und wie die Zubereitung geht.

### Ist-Zustand
- **Speiseplan-PDF:** Nur Rezeptnamen in Tabelle (kein Rezeptinhalt)
- **Rezeptbuch-PDF:** Alle Rezepte nacheinander, ohne Tagesbezug
- Es gibt keine Kombination aus beidem
- Der User nutzt bisher eine Excel-Tabelle mit Reiter "Tageslisten" für diesen Zweck

### Referenz-Layout (aus User-Screenshot)
Das gewünschte Format orientiert sich an der bisherigen Excel-Tagesliste:
```
╔══════════════════════════════════════════════════════════╗
║  Samstag, 10.01.2026                                    ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Frühstück: Creps                                        ║
║  ┌──────────┬──────────────┬─────────────────────────┐   ║
║  │ 1750 g   │ Weizenmehl   │ 1. Mehl, Salz, Eier und │   ║
║  │ 350 g    │ Butter       │    Milch verrühren.      │   ║
║  │ 1400 ml  │ Milch        │ 2. Nach und nach Wasser  │   ║
║  │ 1750 ml  │ Wasser       │    und zerlassene Butter │   ║
║  │ 14       │ Eier         │    zufügen               │   ║
║  │ 7 Prisen │ Salz         │                          │   ║
║  └──────────┴──────────────┴─────────────────────────┘   ║
║                                                          ║
║  Mittag: Pizzasuppe                                      ║
║  ┌──────────┬──────────────┬─────────────────────────┐   ║
║  │ 4,5 kg   │ Hackfleisch  │ 1. Hackfleisch mit      │   ║
║  │ 6,75     │ Zwiebeln     │    Zwiebeln braten.      │   ║
║  │ 9        │ Paprika      │ 2. Paprika würfeln.      │   ║
║  │ ...      │ ...          │ 3. Wasser mit Fleisch-   │   ║
║  │          │              │    brühe anrühren...     │   ║
║  └──────────┴──────────────┴─────────────────────────┘   ║
║                                                          ║
║  Nachtisch: Schneewitchennachtisch                       ║
║  ┌──────────┬────────────────────┬───────────────────┐   ║
║  │ 600 g    │ Zartbitterschoko.. │ 1. Schokolade in  │   ║
║  │ ...      │ ...                │    Stücke teilen.. │   ║
║  └──────────┴────────────────────┴───────────────────┘   ║
║                                                          ║
║  Abendbrot                                               ║
║    Vorspeise: Nachos                                     ║
║    ┌──────────┬──────────────┐                           ║
║    │ 9 Pack.  │ Nachos       │                           ║
║    │ 7 Pack.  │ gerieb. Käse │                           ║
║    │ ...      │ ...          │                           ║
║    └──────────┴──────────────┘                           ║
║    Hauptgang: Kartoffeln mit Hähnchen im Bacon           ║
║    ┌──────────┬──────────────┐                           ║
║    │ 12,31 kg │ Kartoffel    │                           ║
║    │ ...      │ ...          │                           ║
║    └──────────┴──────────────┘                           ║
╚══════════════════════════════════════════════════════════╝
```

**Kernmerkmale aus dem Screenshot:**
- Tagesüberschrift mit Datum + Wochentag
- Mahlzeit-Überschrift mit Rezeptname (z.B. "Frühstück: Creps")
- Zutaten (Menge + Name) und Zubereitung nebeneinander in einer Tabelle
- Mehrere Rezepte pro Mahlzeit möglich (Vorspeise, Hauptgang, Salat beim Abendessen)
- Mengen sind bereits auf Teilnehmerzahl skaliert

### Akzeptanzkriterien
- [ ] Neuer Export-Endpunkt: "Tageslisten" PDF
- [ ] Gliederung: Tag → Mahlzeit → Rezept(e) mit Zutaten und Zubereitung
- [ ] Zutaten und Zubereitungsschritte nebeneinander (3-Spalten-Tabelle: Menge | Zutat | Anleitung)
- [ ] Mehrere Rezepte pro Mahlzeit werden untereinander dargestellt
- [ ] Mengen sind auf `participant_count` (oder `custom_servings` aus Story 1) skaliert
- [ ] Seitenumbruch zwischen Tagen
- [ ] Export-Button in der Wochenübersicht verfügbar ("Tageslisten PDF")

### Technische Umsetzung
- Neuer Endpunkt in `export.py`: `GET /export/daily-lists/pdf/{camp_id}`
- Daten: `meal_plans` nach Datum gruppieren, dann nach MealType sortieren
- Pro Rezept eine Tabelle mit 3 Spalten: Menge+Einheit | Zutatname | Zubereitungsschritte
  - Zubereitungsschritte aus `recipe.instructions` parsen (zeilenweise nummeriert)
  - Schritte auf die Tabellenzeilen verteilen (Schritt 1 in Zeile 1, Schritt 2 in Zeile 2, etc.)
- Falls ein Rezept keine Zubereitung hat: 2-Spalten-Tabelle (nur Menge | Zutat)
- Export-Button in `meal_planning/index.html` hinzufügen

### Sub-Kategorien (Vorspeise/Hauptgang/Salat)
**Entscheidung:** Neues optionales Feld `sub_category` auf MealPlan. Moegliche Werte: Vorspeise, Hauptgang, Beilage, Salat, Nachtisch (oder leer). Braucht DB-Migration und UI-Anpassung (Dropdown beim Zuweisen eines Rezepts zum Abendessen).

---

## Story 4: Rezept-Vorschau in der Wochenübersicht

**Aufwand:** Klein-Mittel | **Machbarkeit:** Sehr gut

### Beschreibung
Als Küchenplaner möchte ich in der Wochenübersicht mit einem Klick auf ein geplantes Rezept einen schnellen Einblick in das Rezept bekommen, ohne die Seite verlassen zu müssen.

### Ist-Zustand
- In der Wochenübersicht steht nur der Rezeptname (truncated)
- Einzige Interaktion: Löschen-Button
- Für Details muss man zur Rezeptseite navigieren (`/recipes/{id}`)

### Akzeptanzkriterien
- [ ] Klick auf ein Rezept in der Wochenübersicht öffnet eine Vorschau
- [ ] Vorschau zeigt: Rezeptname, Beschreibung, Zutaten (skaliert), Zubereitungszeit
- [ ] Vorschau ist schnell schließbar (Klick außerhalb, X-Button, Escape)
- [ ] Optional: Link zur vollständigen Rezeptseite in der Vorschau
- [ ] Funktioniert auf Desktop (Mobile ist nice-to-have)

### Technische Umsetzung
- **Option A: Modal/Dialog** (empfohlen)
  - Alpine.js Modal-Komponente in `meal_planning/index.html`
  - HTMX-Request: `GET /recipes/{id}/preview` → liefert HTML-Fragment
  - Neuer Template-Partial: `templates/recipes/preview_modal.html`
  - Neuer Endpunkt in `recipes.py`: Lightweight-Rezeptdaten für Vorschau

- **Option B: Popover/Tooltip**
  - Erscheint bei Hover/Klick direkt neben dem Rezept
  - Kompakter, aber weniger Platz für Infos

### Hinweis
- Modal ist besser geeignet, da genug Platz für Zutaten + Anleitung
- HTMX macht das Laden des Inhalts einfach (`hx-get`, `hx-target`)

---

## Story 5: Reste-Tracker mit Statistik

**Aufwand:** Gross | **Machbarkeit:** Gut

### Beschreibung
Als Kuechenplaner moechte ich nach jeder Mahlzeit erfassen koennen, was und wie viel uebrig geblieben ist, und ueber mehrere Freizeiten eine Statistik pro Rezept sehen, damit ich beim naechsten Mal besser planen kann.

### Ist-Zustand
- Kein Reste-Tracking in der App
- Wird aktuell manuell (Zettel/Notizen) erfasst

### Geklarte Anforderungen

- **Granularitaet:** Flexibel - je nach Rezept pro Rezept oder pro Zutat. Bei Nachtisch waere pro Zutat unpraktisch, bei Nudeln mit Sosse ist es sinnvoll. Der User waehlt bei jeder Erfassung selbst.
- **Einheit:** Prozent (z.B. "20% uebrig") oder Freitext (z.B. "3kg Nudeln, 2L Sosse")
- **Zeitpunkt:** Nach jeder Mahlzeit - Button "Reste erfassen" pro geplanter Mahlzeit im Kalender
- **Statistik:** Durchschnittliche Restmenge pro Person, pro Rezept ueber mehrere Freizeiten
- **Skalierung:** Nur als Vorschlag anzeigen, nicht automatisch anpassen

### Akzeptanzkriterien
- [ ] Button "Reste erfassen" pro geplanter Mahlzeit in der Wochenuebersicht
- [ ] Erfassungs-Dialog: Auswahl ob pro Rezept oder pro Zutat erfasst wird
- [ ] Prozent-Feld (optional) fuer schnelle Schaetzung (z.B. "20% uebrig")
- [ ] Freitext-Feld fuer Details (z.B. "3kg Nudeln, 2L Sosse")
- [ ] Uebersicht aller erfassten Reste fuer das aktuelle Camp
- [ ] Statistik pro Rezept ueber mehrere Camps hinweg: Durchschnittliche Restmenge pro Person
- [ ] Skalierungs-Vorschlag in der Statistik (z.B. "Naechstes Mal fuer 35 statt 45 Personen skalieren") - nicht automatisch, nur als Hinweis

### Technische Umsetzung

**Neues Model:**
```python
class Leftover(Base):
    __tablename__ = 'leftovers'

    id = Column(Integer, primary_key=True)
    meal_plan_id = Column(Integer, ForeignKey('meal_plans.id'))
    recipe_id = Column(Integer, ForeignKey('recipes.id'))
    camp_id = Column(Integer, ForeignKey('camps.id'))
    tracking_type = Column(String)       # "per_recipe" oder "per_ingredient"
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), nullable=True)  # nur bei per_ingredient
    percentage_left = Column(Float, nullable=True)  # z.B. 20.0 fuer 20%
    description = Column(Text)           # Freitext: "3kg Nudeln, 2L Sosse"
    created_at = Column(DateTime)
```

**Neue Dateien:**
- `app/routers/leftovers.py` - CRUD + Statistik-Endpunkte
- `app/templates/leftovers/index.html` - Uebersicht + Erfassung
- `app/templates/leftovers/statistics.html` - Statistik-Ansicht

**Statistik:**
- Durchschnittliche Restmenge pro Person pro Rezept (ueber alle Camps)
- "Pizzasuppe: In 3 von 5 Freizeiten blieben Reste (Ø 20%)"
- Vorschlag: "Naechstes Mal fuer 35 statt 45 Personen skalieren" (nur Anzeige, kein Auto-Anpassen)

---

## Priorisierungs-Vorschlag

| Prio | Story | Aufwand | Begründung |
|------|-------|---------|------------|
| 1 | Story 2: Kompaktere Einkaufsliste | Klein | Quick Win, sofort spürbar |
| 2 | Story 4: Rezept-Vorschau | Klein-Mittel | Verbessert tägliche Nutzung stark |
| 3 | Story 1: Individuelle Personenanzahl | Mittel | Wichtig für flexible Planung |
| 4 | Story 3: Tageweise Rezept-PDF | Mittel | Layout geklaert (Tages-Kochbuch mit Untergruppen) |
| 5 | Story 5: Reste-Tracker | Gross | Alle Fragen geklaert, groesstes Feature |
