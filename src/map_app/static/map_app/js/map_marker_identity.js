function extractActivityLogIdFromTooltip(marker) {
    var tooltip = marker.getTooltip();
    if (!tooltip || !tooltip._content) return null;

    var container = document.createElement("div");
    container.innerHTML = tooltip._content;
    var element = container.querySelector("[data-activity-log-id], [data-performance-id]");
    if (!element) return null;

    var activityLogId = parseInt(element.dataset.activityLogId || element.dataset.performanceId, 10);
    if (Number.isNaN(activityLogId)) return null;
    return activityLogId;
}

function resolveActivityLogId(marker) {
    if (marker && marker.options) {
        var optionActivityLogId = marker.options.activityLogId || marker.options.activity_log_id || marker.options.performanceId || marker.options.performance_id;
        var parsedOptionId = parseInt(optionActivityLogId, 10);
        if (!Number.isNaN(parsedOptionId)) {
            return parsedOptionId;
        }
    }
    return extractActivityLogIdFromTooltip(marker);
}

var extractPerformanceIdFromTooltip = extractActivityLogIdFromTooltip;
var resolvePerformanceId = resolveActivityLogId;

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

function buildMarkerIdentity(activityLogId, locationId) {
    if (activityLogId && activityLogId > 0) {
        return { type: "activity_log", id: activityLogId };
    }
    if (locationId && locationId > 0) {
        return { type: "location", id: locationId };
    }
    return null;
}
