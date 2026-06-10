/**
 * Recipe Form Components (Alpine.js)
 *
 * Geteiltes Markup/Logik fuer `templates/recipes/create.html` und `edit.html`.
 * Der Modus (create/edit) wird ueber `window.RECIPE_FORM_CONFIG` gesteuert,
 * das im jeweiligen Template gesetzt wird, bevor dieses Skript geladen wird.
 *
 * Erwartete Config:
 *   {
 *     mode: 'create' | 'edit',
 *     submitUrl: string,       // POST/PUT-Ziel
 *     submitMethod: 'POST' | 'PUT',
 *     redirectUrl: string,     // Wohin nach Erfolg
 *     draftKey: string | null, // LocalStorage-Key fuer Entwuerfe (nur create)
 *     initialData: object | null  // Vorbefuellte Form-Daten (nur edit)
 *   }
 */

function ingredientAutocomplete() {
    return {
        search: '',
        suggestions: [],
        showSuggestions: false,
        selectedIndex: -1,

        async searchIngredients() {
            if (this.search.length < 1) {
                this.suggestions = [];
                this.showSuggestions = false;
                return;
            }

            try {
                const response = await fetch(`/recipes/api/ingredients/search?q=${encodeURIComponent(this.search)}`);
                this.suggestions = await response.json();
                this.showSuggestions = true;
                this.selectedIndex = -1;
            } catch (error) {
                window.FreizeitApp.showToast('Suche fehlgeschlagen', 'error');
            }
        },

        selectSuggestion(suggestion) {
            window.dispatchEvent(new CustomEvent('ingredient-selected', {
                detail: {
                    id: suggestion.id,
                    name: suggestion.name,
                    unit: suggestion.unit,
                    category: suggestion.category,
                    category_id: suggestion.category_id ?? null
                }
            }));

            this.search = '';
            this.suggestions = [];
            this.showSuggestions = false;
        },

        navigateDown() {
            if (this.selectedIndex < this.suggestions.length - 1) {
                this.selectedIndex++;
            }
        },

        navigateUp() {
            if (this.selectedIndex > 0) {
                this.selectedIndex--;
            }
        },

        selectCurrent() {
            if (this.selectedIndex >= 0 && this.selectedIndex < this.suggestions.length) {
                this.selectSuggestion(this.suggestions[this.selectedIndex]);
            }
        },

        openNewIngredientModal() {
            window.dispatchEvent(new CustomEvent('open-new-ingredient-modal', {
                detail: { name: this.search }
            }));
        }
    };
}

function newIngredientForm() {
    return {
        newIngredient: {
            name: '',
            unit: '',
            category: ''
        },
        _handleOpenModal: null,

        init() {
            this._handleOpenModal = (e) => {
                this.newIngredient.name = e.detail?.name || '';
            };
            window.addEventListener('open-new-ingredient-modal', this._handleOpenModal);
        },

        destroy() {
            if (this._handleOpenModal) {
                window.removeEventListener('open-new-ingredient-modal', this._handleOpenModal);
            }
        },

        async createNewIngredient() {
            try {
                const formData = new FormData();
                formData.append('name', this.newIngredient.name);
                formData.append('unit', this.newIngredient.unit);
                formData.append('category', this.newIngredient.category);

                const response = await fetch('/recipes/api/ingredients/quick-create', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const ingredient = await response.json();

                    const formElement = document.getElementById('recipe-form');
                    if (formElement && formElement.__x && formElement.__x.$data) {
                        formElement.__x.$data.ensureUnitOption(ingredient.unit);
                        formElement.__x.$data.currentIngredient = {
                            id: ingredient.id,
                            name: ingredient.name,
                            quantity: null,
                            unit: ingredient.unit,
                            customUnit: '',
                            category: ingredient.category,
                            category_id: ingredient.category_id ?? null
                        };
                    }

                    window.dispatchEvent(new CustomEvent('close-new-ingredient-modal'));
                    this.newIngredient = { name: '', unit: '', category: '' };
                    window.FreizeitApp.showToast('Zutat erfolgreich erstellt!', 'success');
                } else {
                    const error = await response.json();
                    window.FreizeitApp.showToast(error.error || 'Fehler beim Erstellen der Zutat', 'error');
                }
            } catch (error) {
                window.FreizeitApp.showToast('Fehler beim Erstellen der Zutat', 'error');
            }
        }
    };
}

function recipeForm() {
    const config = window.RECIPE_FORM_CONFIG || {
        mode: 'create',
        submitUrl: '/recipes/',
        submitMethod: 'POST',
        redirectUrl: '/recipes/',
        draftKey: 'recipe_draft',
        initialData: null
    };

    return {
        config: config,
        categories: config.categories || [],
        formData: config.initialData ? { ...config.initialData } : {
            name: '',
            description: '',
            base_servings: 30,
            preparation_time: null,
            cooking_time: null,
            instructions: '',
            ingredients: [],
            tag_ids: [],
            allergen_ids: []
        },
        currentIngredient: {
            id: null,
            name: '',
            quantity: null,
            unit: '',
            customUnit: '',
            category: '',
            category_id: null
        },
        errors: {},
        isSubmitting: false,
        autoSaveStatus: '',
        sortable: null,
        _handleIngredientSelected: null,

        init() {
            if (this.config.draftKey) {
                this.loadFromLocalStorage();
            }

            this.$nextTick(() => {
                this.initializeSortable();
            });

            this.$watch('formData.ingredients', () => {
                this.$nextTick(() => {
                    this.initializeSortable();
                });
            });

            this._handleIngredientSelected = (event) => {
                this.ensureUnitOption(event.detail.unit);
                this.currentIngredient = {
                    id: event.detail.id,
                    name: event.detail.name,
                    quantity: null,
                    unit: event.detail.unit,
                    customUnit: '',
                    category: event.detail.category,
                    category_id: event.detail.category_id ?? null
                };
            };
            window.addEventListener('ingredient-selected', this._handleIngredientSelected);
        },

        destroy() {
            if (this._handleIngredientSelected) {
                window.removeEventListener('ingredient-selected', this._handleIngredientSelected);
            }
            if (this.config.draftKey) {
                localStorage.removeItem(this.config.draftKey);
            }
        },

        initializeSortable() {
            const categories = this.getIngredientCategories();

            categories.forEach(category => {
                const container = document.querySelector(`[data-category="${category}"]`);
                if (!container) {
                    return;
                }
                if (container.sortableInstance) {
                    container.sortableInstance.destroy();
                }

                const sortableInstance = Sortable.create(container, {
                    animation: 200,
                    handle: 'svg',
                    ghostClass: 'sortable-ghost',
                    chosenClass: 'sortable-chosen',
                    dragClass: 'sortable-drag',
                    onEnd: () => {
                        const items = container.querySelectorAll('[data-ingredient-index]');
                        const newOrder = [];

                        items.forEach(item => {
                            const originalIndex = parseInt(item.getAttribute('data-ingredient-index'));
                            newOrder.push(this.formData.ingredients[originalIndex]);
                        });

                        const otherIngredients = this.formData.ingredients.filter(
                            ing => ing.category !== category
                        );

                        this.formData.ingredients = [...otherIngredients, ...newOrder];

                        if (this.config.draftKey) {
                            this.saveToLocalStorage();
                        }
                    }
                });
                container.sortableInstance = sortableInstance;
            });
        },

        ensureUnitOption(unit) {
            // Make an arbitrary unit (e.g. from a freshly created ingredient that
            // uses neither a standard nor a configured custom unit) selectable by
            // injecting it as an <option> ahead of the "Eigene Einheit..." entry.
            if (!unit) {
                return;
            }
            const select = document.getElementById('ingredient-unit');
            if (!select) {
                return;
            }
            const exists = Array.from(select.options).some(o => o.value === unit);
            if (exists) {
                return;
            }
            const option = document.createElement('option');
            option.value = unit;
            option.textContent = unit;
            const customOption = Array.from(select.options).find(o => o.value === 'custom');
            select.insertBefore(option, customOption || null);
        },

        canAddIngredient() {
            return this.currentIngredient.id &&
                   this.currentIngredient.quantity > 0 &&
                   (this.currentIngredient.unit !== '' || this.currentIngredient.customUnit !== '');
        },

        addIngredient() {
            if (!this.canAddIngredient()) {
                window.FreizeitApp.showToast('Bitte alle Felder ausfuellen', 'warning');
                return;
            }

            const finalUnit = this.currentIngredient.unit === ''
                ? this.currentIngredient.customUnit
                : this.currentIngredient.unit;

            this.formData.ingredients.push({
                ingredient_id: this.currentIngredient.id,
                name: this.currentIngredient.name,
                quantity: this.currentIngredient.quantity,
                unit: finalUnit,
                category: this.currentIngredient.category,
                category_id: this.currentIngredient.category_id ?? null
            });

            window.FreizeitApp.showToast('Zutat hinzugefuegt!', 'success');

            this.currentIngredient = {
                id: null,
                name: '',
                quantity: null,
                unit: '',
                customUnit: '',
                category: '',
                category_id: null
            };

            if (this.config.draftKey) {
                this.saveToLocalStorage();
            }
        },

        removeIngredient(index) {
            this.formData.ingredients.splice(index, 1);
            if (this.config.draftKey) {
                this.saveToLocalStorage();
            }
        },

        getIngredientCategories() {
            const categories = [...new Set(this.formData.ingredients.map(i => i.category))];
            return categories.sort();
        },

        getIngredientsByCategory(category) {
            return this.formData.ingredients.filter(i => i.category === category);
        },

        onIngredientCategoryChange(ingredient, value) {
            const categoryId = value === '' ? null : parseInt(value);
            ingredient.category_id = categoryId;
            const category = this.categories.find(c => c.id === categoryId);
            ingredient.category = category ? category.name : '';
            if (this.config.draftKey) {
                this.saveToLocalStorage();
            }
        },

        validateForm() {
            this.errors = {};

            if (!this.formData.name || this.formData.name.trim() === '') {
                this.errors.name = 'Name ist erforderlich';
            }

            if (this.formData.ingredients.length === 0) {
                this.errors.ingredients = 'Mindestens eine Zutat ist erforderlich';
            }

            if (!this.formData.instructions || this.formData.instructions.trim() === '') {
                this.errors.instructions = 'Anleitung ist erforderlich';
            }

            return Object.keys(this.errors).length === 0;
        },

        async submitForm() {
            if (!this.validateForm()) {
                window.FreizeitApp.showToast('Bitte fuellen Sie alle Pflichtfelder aus', 'error');
                return;
            }

            this.isSubmitting = true;

            try {
                const formData = new FormData();
                formData.append('name', this.formData.name);
                formData.append('description', this.formData.description || '');
                formData.append('base_servings', this.formData.base_servings);

                if (this.formData.preparation_time !== null && this.formData.preparation_time !== '') {
                    formData.append('preparation_time', this.formData.preparation_time);
                }
                if (this.formData.cooking_time !== null && this.formData.cooking_time !== '') {
                    formData.append('cooking_time', this.formData.cooking_time);
                }

                formData.append('instructions', this.formData.instructions);

                formData.append('ingredients', JSON.stringify(
                    this.formData.ingredients.map(ing => ({
                        ingredient_id: ing.ingredient_id,
                        quantity: ing.quantity,
                        unit: ing.unit,
                        category_id: ing.category_id ?? null
                    }))
                ));

                formData.append('tag_ids', JSON.stringify(this.formData.tag_ids));
                formData.append('allergen_ids', JSON.stringify(this.formData.allergen_ids));

                const response = await fetch(this.config.submitUrl, {
                    method: this.config.submitMethod,
                    body: formData
                });

                if (response.ok) {
                    const successMessage = this.config.mode === 'create'
                        ? 'Rezept erfolgreich erstellt!'
                        : 'Rezept erfolgreich aktualisiert!';
                    window.FreizeitApp.showToast(successMessage, 'success');

                    if (this.config.draftKey) {
                        localStorage.removeItem(this.config.draftKey);
                    }

                    setTimeout(() => {
                        window.location.href = this.config.redirectUrl;
                    }, 1000);
                } else {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || 'Server error');
                }
            } catch (error) {
                window.FreizeitApp.showToast(`Fehler beim Speichern des Rezepts: ${error.message}`, 'error');
            } finally {
                this.isSubmitting = false;
            }
        },

        saveToLocalStorage() {
            if (!this.config.draftKey) {
                return;
            }
            localStorage.setItem(this.config.draftKey, JSON.stringify(this.formData));
            this.autoSaveStatus = 'Entwurf gespeichert um ' + new Date().toLocaleTimeString();

            setTimeout(() => {
                this.autoSaveStatus = '';
            }, 3000);
        },

        loadFromLocalStorage() {
            if (!this.config.draftKey) {
                return;
            }
            const draft = localStorage.getItem(this.config.draftKey);
            if (!draft) {
                return;
            }
            try {
                const parsed = JSON.parse(draft);
                if (confirm('Es wurde ein Entwurf gefunden. Moechten Sie diesen wiederherstellen?')) {
                    this.formData = parsed;
                } else {
                    localStorage.removeItem(this.config.draftKey);
                }
            } catch (error) {
                localStorage.removeItem(this.config.draftKey);
            }
        }
    };
}
