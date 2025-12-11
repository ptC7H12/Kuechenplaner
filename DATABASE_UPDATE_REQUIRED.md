# Datenbank-Update erforderlich

## Problem
Das Datenbank-Schema wurde geändert: `meal_plans.recipe_id` ist jetzt `nullable=True`, um "Kein Essen"-Einträge zu unterstützen.

## Lösung (Daten gehen verloren)
1. Anwendung schließen
2. Datenbank-Datei löschen:
   - Windows: `kuechenplaner.db` im Anwendungsverzeichnis oder `%APPDATA%\Kuechenplaner\`
   - Linux: `kuechenplaner.db` im Projektverzeichnis
3. Anwendung neu starten (DB wird automatisch neu erstellt)

## Alternative: Daten behalten mit Alembic-Migration

Falls Sie Ihre Daten behalten möchten:

```bash
# 1. Migration erstellen
alembic revision --autogenerate -m "Make recipe_id nullable in meal_plans"

# 2. Migration anpassen (alembic/versions/xxx_make_recipe_id_nullable.py):
def upgrade():
    # SQLite unterstützt ALTER COLUMN nicht direkt
    # Wir müssen die Tabelle neu erstellen
    op.execute("""
        CREATE TABLE meal_plans_new (
            id INTEGER PRIMARY KEY,
            camp_id INTEGER NOT NULL,
            recipe_id INTEGER,  -- Jetzt nullable
            meal_date DATETIME NOT NULL,
            meal_type VARCHAR(50) NOT NULL,
            position INTEGER DEFAULT 0,
            notes TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY(camp_id) REFERENCES camps(id),
            FOREIGN KEY(recipe_id) REFERENCES recipes(id)
        )
    """)
    
    op.execute("INSERT INTO meal_plans_new SELECT * FROM meal_plans")
    op.execute("DROP TABLE meal_plans")
    op.execute("ALTER TABLE meal_plans_new RENAME TO meal_plans")

def downgrade():
    pass

# 3. Migration ausführen
alembic upgrade head
```

## Schema-Änderung
```python
# Vorher
recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)

# Nachher
recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=True)
```
