(function(global) {
    function createMapSearchEvents(deps) {
        var elements = deps.elements;
        var store = deps.store;
        var searchState = deps.searchState;
        var config = deps.config;
        var onFiltersChanged = deps.onFiltersChanged;
        var headerUi = deps.headerUi;
        var urlSync = deps.urlSync;

        function bindInputEvents() {
            if (!elements.queryInput) return;

            elements.queryInput.addEventListener("compositionstart", function() {
                store.setIsComposing(true);
            });

            elements.queryInput.addEventListener("compositionend", function() {
                store.setIsComposing(false);
                onFiltersChanged(config.delays.input);
            });

            elements.queryInput.addEventListener("input", function() {
                if (store.isComposing()) return;
                onFiltersChanged(config.delays.input);
            });
        }

        function bindFormEvents() {
            elements.form.addEventListener("submit", function(event) {
                event.preventDefault();
                onFiltersChanged(config.delays.submit);
            });

            elements.tagCheckboxes.forEach(function(checkbox) {
                checkbox.addEventListener("change", function() {
                    onFiltersChanged(config.delays.tagChange);
                });
            });

            if (elements.selectedTagList) {
                elements.selectedTagList.addEventListener("click", function(event) {
                    var clearAllButton = event.target.closest("[data-tag-clear-all]");
                    if (clearAllButton) {
                        event.preventDefault();
                        searchState.clearAllTags();
                        onFiltersChanged(config.delays.submit);
                        return;
                    }

                    var button = event.target.closest("[data-tag-remove]");
                    if (!button) return;

                    event.preventDefault();
                    var targetTag = button.getAttribute("data-tag-remove");
                    var targetCheckbox = null;
                    elements.tagCheckboxes.forEach(function(checkbox) {
                        if (checkbox.value === targetTag) {
                            targetCheckbox = checkbox;
                        }
                    });
                    if (!targetCheckbox || !targetCheckbox.checked) return;

                    targetCheckbox.checked = false;
                    onFiltersChanged(config.delays.tagRemove);
                });
            }

            if (elements.queryClearButton) {
                elements.queryClearButton.addEventListener("click", function(event) {
                    event.preventDefault();
                    if (!elements.queryInput) return;
                    elements.queryInput.value = "";
                    onFiltersChanged(config.delays.submit);
                });
            }
        }

        function bindTagPanelBehavior() {
            if (!elements.tagFilter) return;

            urlSync.consumeLegacyKeepOpenParam(function() {
                headerUi.setSearchPanelOpen(true);
                elements.tagFilter.setAttribute("open", "");
            });

            function closeTagPanelOnOutsideInteraction(event) {
                if (!elements.tagFilter.open) return;
                if (elements.tagFilter.contains(event.target)) return;
                elements.tagFilter.removeAttribute("open");
            }

            document.addEventListener("pointerdown", closeTagPanelOnOutsideInteraction, true);
            document.addEventListener("touchstart", closeTagPanelOnOutsideInteraction, true);
            document.addEventListener("click", closeTagPanelOnOutsideInteraction, true);
        }

        return {
            bindInputEvents: bindInputEvents,
            bindFormEvents: bindFormEvents,
            bindTagPanelBehavior: bindTagPanelBehavior,
        };
    }

    global.MapSearchEvents = {
        create: createMapSearchEvents,
    };
})(window);
