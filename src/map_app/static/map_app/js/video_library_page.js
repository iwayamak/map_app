document.addEventListener("DOMContentLoaded", function() {
    var searchPanelStateKey = "video_library_search_open";
    var toggleButton = document.getElementById("search-toggle-button");
    var searchContainer = document.getElementById("map-search-container");
    var searchForm = document.getElementById("video-search-form");

    if (!toggleButton || !searchContainer || !searchForm) return;

    var queryInput = searchForm.querySelector(".map-search-input");
    var clearButton = document.getElementById("map-search-input-clear");
    var debounceTimer = null;
    var isComposing = false;

    function syncClearButton() {
        if (!clearButton || !queryInput) return;
        clearButton.classList.toggle("is-hidden", !queryInput.value.trim());
    }

    function syncSearchBadge() {
        var hasQuery = Boolean(queryInput && queryInput.value.trim());
        var isOpen = searchContainer.classList.contains("is-open");
        toggleButton.classList.toggle("has-filter-badge", hasQuery && !isOpen);
    }

    function persistSearchOpen(isOpen) {
        try {
            if (isOpen) {
                window.sessionStorage.setItem(searchPanelStateKey, "1");
            } else {
                window.sessionStorage.removeItem(searchPanelStateKey);
            }
        } catch (error) {
            void error;
        }
    }

    function submitSearch() {
        var nextUrl = new URL(window.location.href);
        var query = queryInput ? queryInput.value.trim() : "";
        if (query) {
            nextUrl.searchParams.set("q", query);
        } else {
            nextUrl.searchParams.delete("q");
        }
        nextUrl.searchParams.delete("page");
        if (window.MapAppPageLoading && typeof window.MapAppPageLoading.navigate === "function") {
            window.MapAppPageLoading.navigate(nextUrl.toString(), { title: "読み込み中" });
            return;
        }
        window.location.assign(nextUrl.toString());
    }

    function setSearchOpen(isOpen) {
        searchContainer.classList.toggle("is-open", isOpen);
        toggleButton.setAttribute("aria-expanded", isOpen ? "true" : "false");
        persistSearchOpen(isOpen);
        syncSearchBadge();
    }

    toggleButton.addEventListener("click", function() {
        var nextOpen = !searchContainer.classList.contains("is-open");
        setSearchOpen(nextOpen);
        if (nextOpen && queryInput) {
            queryInput.focus();
        }
    });

    if (queryInput) {
        queryInput.addEventListener("compositionstart", function() {
            isComposing = true;
        });
        queryInput.addEventListener("compositionend", function() {
            isComposing = false;
            syncClearButton();
            syncSearchBadge();
            window.clearTimeout(debounceTimer);
            debounceTimer = window.setTimeout(submitSearch, 260);
        });
        queryInput.addEventListener("input", function() {
            syncClearButton();
            syncSearchBadge();
            if (isComposing) return;
            window.clearTimeout(debounceTimer);
            debounceTimer = window.setTimeout(submitSearch, 260);
        });
        queryInput.addEventListener("keydown", function(event) {
            if (event.key !== "Enter" || isComposing) return;
            event.preventDefault();
            window.clearTimeout(debounceTimer);
            submitSearch();
        });
    }

    if (clearButton && queryInput) {
        clearButton.addEventListener("click", function() {
            window.clearTimeout(debounceTimer);
            queryInput.value = "";
            syncClearButton();
            syncSearchBadge();
            persistSearchOpen(true);
            submitSearch();
        });
    }

    try {
        if (window.sessionStorage.getItem(searchPanelStateKey) === "1") {
            setSearchOpen(true);
        }
    } catch (error) {
        void error;
    }

    syncClearButton();
    syncSearchBadge();
});
