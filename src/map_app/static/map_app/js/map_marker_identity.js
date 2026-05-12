function extractPerformanceIdFromTooltip(marker) {
    var tooltip = marker.getTooltip();
    if (!tooltip || !tooltip._content) return null;

    var container = document.createElement("div");
    container.innerHTML = tooltip._content;
    var element = container.querySelector("[data-performance-id]");
    if (!element || !element.dataset.performanceId) return null;

    var performanceId = parseInt(element.dataset.performanceId, 10);
    if (Number.isNaN(performanceId)) return null;
    return performanceId;
}

function resolvePerformanceId(marker) {
    if (marker && marker.options) {
        var optionPerformanceId = marker.options.performanceId || marker.options.performance_id;
        var parsedOptionId = parseInt(optionPerformanceId, 10);
        if (!Number.isNaN(parsedOptionId)) {
            return parsedOptionId;
        }
    }
    return extractPerformanceIdFromTooltip(marker);
}

function resolveLocationId(marker) {
    if (marker && marker.options) {
        var optionLocationId = marker.options.locationId || marker.options.location_id;
        var parsedOptionId = parseInt(optionLocationId, 10);
        if (!Number.isNaN(parsedOptionId)) {
            return parsedOptionId;
        }
    }
    return null;
}

function buildMarkerIdentity(performanceId, locationId) {
    if (performanceId && performanceId > 0) {
        return { type: "performance", id: performanceId };
    }
    if (locationId && locationId > 0) {
        return { type: "location", id: locationId };
    }
    return null;
}
