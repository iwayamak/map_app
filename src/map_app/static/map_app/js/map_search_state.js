(function(global) {
    function createSearchState(elements) {
        function getSelectedCheckboxes() {
            var selected = [];
            elements.tagCheckboxes.forEach(function(checkbox) {
                if (checkbox.checked) selected.push(checkbox);
            });
            return selected;
        }

        function hasQuery() {
            return elements.queryInput ? elements.queryInput.value.trim().length > 0 : false;
        }

        function hasActiveFilters() {
            return hasQuery() || getSelectedCheckboxes().length > 0;
        }

        function buildSearchParams() {
            var params = new URLSearchParams();
            var query = elements.queryInput ? elements.queryInput.value.trim() : "";
            if (query) {
                params.set("q", query);
            }
            getSelectedCheckboxes().forEach(function(checkbox) {
                params.append("tags", checkbox.value);
            });
            return params;
        }

        function clearAllTags() {
            elements.tagCheckboxes.forEach(function(checkbox) {
                checkbox.checked = false;
            });
        }

        function clearAllFilters() {
            if (elements.queryInput) {
                elements.queryInput.value = "";
            }
            clearAllTags();
            if (elements.tagFilter) {
                elements.tagFilter.removeAttribute("open");
            }
        }

        return {
            getSelectedCheckboxes: getSelectedCheckboxes,
            hasQuery: hasQuery,
            hasActiveFilters: hasActiveFilters,
            buildSearchParams: buildSearchParams,
            clearAllTags: clearAllTags,
            clearAllFilters: clearAllFilters,
        };
    }

    global.MapSearchState = {
        create: createSearchState,
    };
})(window);
