function setupAutoSearch() {
    var form = document.getElementById("map-search-form");
    if (!form) return;

    var config = {
        searchApiUrl: "/api/map/search/",
        searchPanelStateKey: "map_search_panel_open",
        legacyKeepOpenParam: "keep_tags_open",
        delays: {
            input: 260,
            tagChange: 120,
            tagRemove: 80,
            submit: 0,
        },
    };

    var elements = {
        form: form,
        searchContainer: document.getElementById("map-search-container"),
        searchToggleButton: document.getElementById("search-toggle-button"),
        queryInput: form.querySelector(".map-search-input"),
        queryClearButton: form.querySelector("#map-search-input-clear"),
        tagFilter: form.querySelector(".map-tag-filter"),
        tagCheckboxes: form.querySelectorAll('input[name="tags"]'),
        selectedTagList: form.querySelector(".map-tag-selected-list"),
        summaryTotalLocations: document.getElementById("summary-total-locations"),
        summaryTaggedLocations: document.getElementById("summary-tagged-locations"),
        summaryTotalPerformances: document.getElementById("summary-total-performances"),
        liveLocationsCount: document.getElementById("map-live-locations-count"),
        livePerformancesCount: document.getElementById("map-live-performances-count"),
    };

    var utils = window.MapSearchUtils;
    if (
        !utils ||
        !window.MapSearchStore ||
        !window.MapSearchState ||
        !window.MapSearchTagPanelUi ||
        !window.MapSearchSummaryUi ||
        !window.MapSearchApi ||
        !window.MapSearchHeaderUi ||
        !window.MapSearchUrlSync ||
        !window.MapSearchEvents
    ) {
        console.error("Map search modules failed to load.");
        return;
    }
    var store = window.MapSearchStore.create();
    var searchState = window.MapSearchState.create(elements);
    var tagPanelUi = window.MapSearchTagPanelUi.create(elements, searchState, utils);
    var summaryUi = window.MapSearchSummaryUi.create(elements);
    var headerUi = window.MapSearchHeaderUi.create(elements, config, utils, store);
    var urlSync = window.MapSearchUrlSync.create(config, utils);

    function syncQueryClearButtonState() {
        if (!elements.queryClearButton) return;
        elements.queryClearButton.classList.toggle("is-hidden", !store.hasQuery());
    }

    function applySearchPayload(payload) {
        if (!payload || typeof payload !== "object") return;

        if (typeof replaceMapMarkers === "function") {
            replaceMapMarkers(payload.markers || []);
        }
        summaryUi.apply(payload.summary);
        if (typeof window.updateStatisticsPanelData === "function") {
            window.updateStatisticsPanelData(payload.statistics);
        }
    }

    var searchApi = window.MapSearchApi.create(config, searchState, store, {
        onSuccess: function(payload, params) {
            applySearchPayload(payload);
            urlSync.replaceFromParams(params);
        },
        onError: function(error) {
            console.error(error);
        },
    });

    function scheduleSearch(delayMs) {
        store.clearDebounceTimer();
        store.setDebounceTimer(setTimeout(searchApi.run, delayMs));
    }

    function applyFilters(options) {
        var nextOptions = options || {};
        var nextQuery = typeof nextOptions.query === "string" ? nextOptions.query : "";
        var nextTags = Array.isArray(nextOptions.tags) ? nextOptions.tags : [];
        var keepPanelState = Boolean(nextOptions.keepPanelState);
        var delayMs = typeof nextOptions.delayMs === "number" ? nextOptions.delayMs : config.delays.submit;

        if (elements.queryInput) {
            elements.queryInput.value = nextQuery;
        }
        searchState.clearAllTags();
        elements.tagCheckboxes.forEach(function(checkbox) {
            checkbox.checked = nextTags.indexOf(checkbox.value) !== -1;
        });

        store.syncFilterUiFromSearchState(searchState);
        tagPanelUi.sync();
        syncQueryClearButtonState();
        headerUi.syncSearchFilterIndicator();

        if (!keepPanelState) {
            headerUi.setSearchPanelOpen(true);
        }
        if (nextOptions.resetMapView && typeof window.resetMapViewToDefault === "function") {
            window.resetMapViewToDefault();
        }

        scheduleSearch(delayMs);
    }

    function onFiltersChanged(delayMs) {
        store.syncFilterUiFromSearchState(searchState);
        headerUi.setSearchPanelOpen(true);
        tagPanelUi.sync();
        syncQueryClearButtonState();
        headerUi.syncSearchFilterIndicator();
        scheduleSearch(delayMs);
    }

    var events = window.MapSearchEvents.create({
        elements: elements,
        store: store,
        searchState: searchState,
        config: config,
        onFiltersChanged: onFiltersChanged,
        headerUi: headerUi,
        urlSync: urlSync,
    });

    events.bindInputEvents();
    events.bindFormEvents();
    headerUi.bindSearchPanelToggle();
    events.bindTagPanelBehavior();
    store.syncFilterUiFromSearchState(searchState);
    tagPanelUi.sync();
    syncQueryClearButtonState();
    headerUi.syncSearchFilterIndicator();
    summaryUi.syncFromCurrentSummaryDom();

    // If initial HTML was rendered without markers, hydrate map+summary from API immediately.
    if (
        typeof globalMarkerClusterGroup !== "undefined" &&
        globalMarkerClusterGroup &&
        typeof globalMarkerClusterGroup.getLayers === "function" &&
        globalMarkerClusterGroup.getLayers().length === 0
    ) {
        scheduleSearch(0);
    }

    window.MapSearchPublicApi = window.MapSearchPublicApi || {};
    window.MapSearchPublicApi.applyFilters = applyFilters;
}

document.addEventListener("DOMContentLoaded", setupAutoSearch);
