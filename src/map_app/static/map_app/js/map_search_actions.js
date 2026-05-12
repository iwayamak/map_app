(function(global) {
    function applyTagFilterFromModal(tagName) {
        var publicApi = global.MapSearchPublicApi;
        if (!tagName || !publicApi || typeof publicApi.applyFilters !== "function") return;
        publicApi.applyFilters({
            query: "",
            tags: [tagName],
            keepPanelState: true,
            resetMapView: true,
            delayMs: 0,
        });
    }

    global.MapSearchActions = {
        applyTagFilterFromModal: applyTagFilterFromModal,
    };
})(window);
