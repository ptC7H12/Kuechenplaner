# Küchenplaner — Claude Code Guide

Mirrors `.cursor/rules/*.mdc` so Claude Code picks up the same conventions.

## Project identity

Desktop camp/recipe planner: **FastAPI + Jinja2 + HTMX + Alpine.js + Tailwind**, **SQLite + SQLAlchemy**, optional **pywebview** shell. Dev server: port **12000** (`DEVELOPMENT=1 python -m app.main`). Entry: `app/main.py`.

## Domain essentials

- **Camp** is the tenancy boundary. Active camp via cookie `current_camp_id` + `get_current_camp` / `require_current_camp` in `app/dependencies.py`. Camp-scoped pages must use these dependencies, not ad-hoc cookie reads.
- **Recipe scaling** (never reimplement elsewhere):
  - `effective_servings = meal_plan.custom_servings or camp.participant_count`
  - `scaling_factor = effective_servings / recipe.base_servings`
  - Use `app/services/calculation.py` and `app/services/unit_converter.py` for lists, exports, and PDFs.
- **Recipe versioning:** every recipe update creates a new `RecipeVersion` snapshot; `MealPlan` references live `Recipe` rows (no meal-plan snapshot).
- **Sub-categories:** validate against `constants.MEAL_SUB_CATEGORIES` in Pydantic (`schemas.py`).

## Language & UX

- **User-facing copy** (templates, toasts, PDF labels): **German**.
- **Code** (identifiers, logs, commit messages): **English**, matching existing style.

## Do not touch (unless explicitly asked)

- Generated/build artifacts: `build/`, `dist/`, `releases/`, `.download_cache/`, `installer/` (release skill handles uploads).
- `alembic/versions/*.py` except when adding a **new** migration alongside `models.py` changes.
- Version bumps / release merges: use skills `new-version` and `create-release` — do not invent alternate versioning.

## Backend conventions

### Layer responsibilities

| Layer | Location | Responsibility |
|-------|----------|----------------|
| HTTP | `app/routers/*.py` | Routes, request/response, HTMX headers, template rendering |
| Validation | `app/schemas.py` | Pydantic models, validators (e.g. `sub_category`, leftover `percentage_left`) |
| Persistence | `app/crud.py` | All DB reads/writes; fuzzy ingredient search (`thefuzz`) |
| Business logic | `app/services/` | Scaling, shopping list aggregation, leftover statistics, units |
| Models | `app/models.py` | SQLAlchemy only — no HTTP or template logic |

**Anti-patterns:** business math in routers; raw SQL in routers; new DB access outside `crud.py`.

### FastAPI patterns

- Register new routers in `app/main.py` via `app.include_router`.
- Reuse `templates` and `get_template_context` from `app/dependencies.py` — do not create second `Jinja2Templates` instances.
- `Depends(get_db)` for sessions; `require_current_camp` when camp is mandatory.
- Idiomatic FastAPI defaults (`Depends()`, `Field()`) are allowed (Ruff `B008` ignored project-wide).

### Key services (extend, don't fork)

- `services/calculation.py` — `scale_recipe`, `calculate_shopping_list` (per-meal `custom_servings`, notes enrichment), `get_camp_statistics`.
- `services/leftover_statistics.py` — cross-camp leftover aggregates and `suggested_servings`.
- `services/unit_converter.py` — g↔kg, ml↔L, TL↔EL; best-unit at ≥1000.

### HTMX response patterns

| Situation | Response |
|-----------|----------|
| HTMX DELETE, no body | `HTMLResponse(content="", status_code=200)` |
| Full page reload | `Response(headers={"HX-Refresh": "true"})` |
| Redirect after HTMX action | `Response(headers={"HX-Redirect": "/path"})` |
| Normal form redirect | `RedirectResponse(url="...", status_code=303)` |
| Partial update | `HTMLResponse(content=fragment)` |

### New feature checklist

1. Model change → Alembic migration (see database section).
2. `schemas.py` + `crud.py` + `services/` as needed.
3. Router endpoint in the appropriate `app/routers/` module.
4. Focused pytest in `tests/` (in-memory DB).

## Frontend (server-rendered)

### Stack

- **Templates:** Jinja2 under `app/templates/`; extend `base.html` for full pages.
- **Interactivity:** HTMX first (partials, `hx-*`); Alpine for local state; **no SPA frameworks**.
- **Styling:** Tailwind utility classes + design tokens in `app/static/css/custom.css`. See `docs/DESIGN_SYSTEM.md` for Material 3 classes (`.btn-primary`, `.form-input`, `.card`, FABs).

### Global UI infrastructure (`base.html`)

- Single `#global-modal` — open via `FreizeitApp.openModal(url)`; endpoint returns **HTML fragment only** (no `{% extends %}`).
- Helpers: `showToast`, `closeModal`, `saveShoppingListNote` (PUT JSON `{note}`).
- `layout.js` on every page; recipe create/edit uses shared `recipe-form.js` + `window.RECIPE_FORM_CONFIG`.

### Patterns to follow

- **Modal fragments:** `GET /recipes/{id}/preview`, `GET /leftovers/new?meal_plan_id=` — return partial templates only.
- **Recipe form:** change `_form.html` + `recipe-form.js` + `RECIPE_FORM_CONFIG` in create/edit wrappers — not duplicate forms.
- **Forms:** reuse macros from `components/forms.html` (`text_input`, `number_input`, etc.) for static fields.
- **HTMX:** debounced search (`keyup changed delay:300ms`), explicit `hx-target` / `hx-swap`.
- **Meal planning:** preserve SortableJS drag-and-drop; suppress click-to-preview during drag on planned cards.
- **Accessibility:** icon-only buttons need `aria-label`; decorative SVGs `aria-hidden="true"`.

### Alpine placement

- Page-specific small components may live inline (e.g. `recipeList()` on list page).
- Reusable or large components → `app/static/js/*.js` (like `recipe-form.js`), loaded from template.

### Anti-patterns

- Full HTML documents for modal endpoints.
- Inline `<script>` blocks growing beyond config objects.
- Duplicating scaling math in templates — compute in services, pass values in context.

## Database & migrations

### Schema authority

- **Alembic is the only schema source at runtime.** `Base.metadata.create_all()` is NOT used on app startup (`run_migrations()` in `app/database.py` via lifespan in `app/main.py`).
- Changing `app/models.py` **without** a new file in `alembic/versions/` leaves user DBs broken — always ship both together.

### Paths

- Dev DB: `data/app.db`
- Prod: `%APPDATA%/KuechenApp/app.db` (Windows) or XDG/`~/.local/share/KuechenApp/` (Linux)
- Backups: `<DATA_DIR>/backups/` (daily, max 7) — triggered on startup, not in tests

### Migration workflow

```bash
# After editing models.py:
alembic revision --autogenerate -m "short description"
# Review generated script — autogenerate misses CHECK constraints, ENUMs, some renames
alembic upgrade head
alembic downgrade -1 && alembic upgrade head   # verify round-trip locally
```

## Quality & development

Before finishing a change:

```bash
python -m pytest tests/ -q
python -m ruff check app tests
python -m ruff format app tests
# Optional for typed code paths:
python -m mypy app
```

## When unsure

Read `TECHNICAL_README.md` before large changes (new entities, export formats, migration strategy).


# Claude rules
## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.
