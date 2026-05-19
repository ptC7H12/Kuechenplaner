# Story 5: Reste-Tracker mit Statistik

**Status:** Done
**Aufwand:** Groß
**Machbarkeit:** Gut
**Implementiert in:** `app/models.py:200-217` (`Leftover`), `alembic/versions/006_leftovers.py`, `app/routers/leftovers.py`, `app/templates/leftovers/`, `app/services/leftover_statistics.py`, `tests/test_leftovers.py`

## Beschreibung

Als Küchenplaner möchte ich nach jeder Mahlzeit erfassen können, was und wie viel übrig geblieben ist, und über mehrere Freizeiten eine Statistik pro Rezept sehen, damit ich beim nächsten Mal besser planen kann.

## Ist-Zustand

- Kein Reste-Tracking in der App
- Wird aktuell manuell (Zettel/Notizen) erfasst

## Geklärte Anforderungen

- **Granularität:** Flexibel - je nach Rezept pro Rezept oder pro Zutat. Bei Nachtisch wäre pro Zutat unpraktisch, bei Nudeln mit Sosse ist es sinnvoll. Der User wählt bei jeder Erfassung selbst.
- **Einheit:** Prozent (z.B. "20% übrig") oder Freitext (z.B. "3kg Nudeln, 2L Sosse")
- **Zeitpunkt:** Nach jeder Mahlzeit - Button "Reste erfassen" pro geplanter Mahlzeit im Kalender
- **Statistik:** Durchschnittliche Restmenge pro Person, pro Rezept über mehrere Freizeiten
- **Skalierung:** Nur als Vorschlag anzeigen, nicht automatisch anpassen

## Akzeptanzkriterien

- [x] Button "Reste erfassen" pro geplanter Mahlzeit in der Wochenübersicht
- [x] Erfassungs-Dialog: Auswahl ob pro Rezept oder pro Zutat erfasst wird
- [x] Prozent-Feld (optional) für schnelle Schätzung (z.B. "20% übrig")
- [x] Freitext-Feld für Details (z.B. "3kg Nudeln, 2L Sosse")
- [x] Übersicht aller erfassten Reste für das aktuelle Camp
- [x] Statistik pro Rezept über mehrere Camps hinweg: Durchschnittliche Restmenge pro Person
- [x] Skalierungs-Vorschlag in der Statistik (z.B. "Nächstes Mal für 35 statt 45 Personen skalieren") - nicht automatisch, nur als Hinweis

## Technische Umsetzung

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
    percentage_left = Column(Float, nullable=True)  # z.B. 20.0 für 20%
    description = Column(Text)           # Freitext: "3kg Nudeln, 2L Sosse"
    created_at = Column(DateTime)
```

**Neue Dateien:**

- `app/routers/leftovers.py` - CRUD + Statistik-Endpunkte
- `app/templates/leftovers/index.html` - Übersicht + Erfassung
- `app/templates/leftovers/statistics.html` - Statistik-Ansicht

**Statistik:**

- Durchschnittliche Restmenge pro Person pro Rezept (über alle Camps)
- "Pizzasuppe: In 3 von 5 Freizeiten blieben Reste (Ø 20%)"
- Vorschlag: "Nächstes Mal für 35 statt 45 Personen skalieren" (nur Anzeige, kein Auto-Anpassen)
