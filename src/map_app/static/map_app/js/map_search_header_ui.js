(function(global) {
    function createHeaderUi(elements, config, utils, store) {
        function syncSearchFilterIndicator() {
            if (!elements.searchToggleButton || !elements.searchContainer || !store) return;
            var filterCount = store.getSelectedTagCount() + (store.hasQuery() ? 1 : 0);
            var isOpen = elements.searchContainer.classList.contains("is-open");
            var shouldShowBadge = filterCount > 0 && !isOpen;
            elements.searchToggleButton.classList.toggle("has-filter-badge", shouldShowBadge);
            if (shouldShowBadge) {
                elements.searchToggleButton.setAttribute("data-filter-count", String(filterCount));
            } else {
                elements.searchToggleButton.removeAttribute("data-filter-count");
            }
        }

        function setSearchPanelOpen(isOpen) {
            if (!elements.searchContainer || !elements.searchToggleButton) return;

            if (isOpen) {
                elements.searchContainer.classList.add("is-open");
                elements.searchToggleButton.setAttribute("aria-expanded", "true");
                elements.searchToggleButton.setAttribute("aria-label", "検索を隠す");
            } else {
                elements.searchContainer.classList.remove("is-open");
                elements.searchToggleButton.setAttribute("aria-expanded", "false");
                elements.searchToggleButton.setAttribute("aria-label", "検索を表示");
                if (elements.tagFilter) {
                    elements.tagFilter.removeAttribute("open");
                }
            }
            utils.writeSearchPanelState(config.searchPanelStateKey, isOpen);
            if (store) {
                store.setSearchPanelOpen(isOpen);
            }
            syncSearchFilterIndicator();
            if (typeof window.requestMapInvalidate === "function") {
                window.requestMapInvalidate({ delayed: true });
            }
        }

        function bindSearchPanelToggle() {
            if (!elements.searchToggleButton || !elements.searchContainer) return;

            elements.searchToggleButton.addEventListener("click", function() {
                var isOpen = elements.searchContainer.classList.contains("is-open");
                setSearchPanelOpen(!isOpen);
            });

            if (store && store.hasSearchPanelOpenState()) {
                setSearchPanelOpen(store.isSearchPanelOpen());
                return;
            }
            setSearchPanelOpen(utils.readSearchPanelState(config.searchPanelStateKey));
        }

        return {
            setSearchPanelOpen: setSearchPanelOpen,
            syncSearchFilterIndicator: syncSearchFilterIndicator,
            bindSearchPanelToggle: bindSearchPanelToggle,
        };
    }

    global.MapSearchHeaderUi = {
        create: createHeaderUi,
    };
})(window);
