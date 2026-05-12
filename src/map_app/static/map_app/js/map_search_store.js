(function(global) {
    function createSearchStore() {
        var state = {
            isComposing: false,
            debounceTimer: null,
            activeRequestController: null,
            activeRequestToken: 0,
            hasQuery: false,
            selectedTagCount: 0,
            hasSearchPanelOpenState: false,
            searchPanelOpen: false,
        };

        function setIsComposing(value) {
            state.isComposing = Boolean(value);
        }

        function isComposing() {
            return state.isComposing;
        }

        function setDebounceTimer(timer) {
            state.debounceTimer = timer || null;
        }

        function getDebounceTimer() {
            return state.debounceTimer;
        }

        function clearDebounceTimer() {
            if (!state.debounceTimer) return;
            clearTimeout(state.debounceTimer);
            state.debounceTimer = null;
        }

        function setActiveRequestController(controller) {
            state.activeRequestController = controller || null;
        }

        function getActiveRequestController() {
            return state.activeRequestController;
        }

        function nextRequestToken() {
            state.activeRequestToken += 1;
            return state.activeRequestToken;
        }

        function isLatestRequestToken(token) {
            return token === state.activeRequestToken;
        }

        function syncFilterUiFromSearchState(searchState) {
            state.hasQuery = searchState.hasQuery();
            state.selectedTagCount = searchState.getSelectedCheckboxes().length;
        }

        function hasQuery() {
            return state.hasQuery;
        }

        function getSelectedTagCount() {
            return state.selectedTagCount;
        }

        function setSearchPanelOpen(value) {
            state.hasSearchPanelOpenState = true;
            state.searchPanelOpen = Boolean(value);
        }

        function hasSearchPanelOpenState() {
            return state.hasSearchPanelOpenState;
        }

        function isSearchPanelOpen() {
            return state.searchPanelOpen;
        }

        return {
            setIsComposing: setIsComposing,
            isComposing: isComposing,
            setDebounceTimer: setDebounceTimer,
            getDebounceTimer: getDebounceTimer,
            clearDebounceTimer: clearDebounceTimer,
            setActiveRequestController: setActiveRequestController,
            getActiveRequestController: getActiveRequestController,
            nextRequestToken: nextRequestToken,
            isLatestRequestToken: isLatestRequestToken,
            syncFilterUiFromSearchState: syncFilterUiFromSearchState,
            hasQuery: hasQuery,
            getSelectedTagCount: getSelectedTagCount,
            setSearchPanelOpen: setSearchPanelOpen,
            hasSearchPanelOpenState: hasSearchPanelOpenState,
            isSearchPanelOpen: isSearchPanelOpen,
        };
    }

    global.MapSearchStore = {
        create: createSearchStore,
    };
})(window);
