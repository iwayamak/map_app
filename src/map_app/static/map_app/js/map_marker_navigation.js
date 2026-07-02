window.__mapAppInitialActivityLogId = window.__mapAppInitialActivityLogId || new URLSearchParams(window.location.search || "").get("activity_log_id") || "";

function zoomToLocation(lat, lng) {
    if (!globalMapInstance) return;
    var spiderfyTriggered = false;
    var triggerSpiderfy = function() {
        if (spiderfyTriggered) return;
        spiderfyTriggered = true;
        requestSpiderfyAtLocation(lat, lng, { forceCenter: true });
    };

    globalMapInstance.once("moveend", triggerSpiderfy);
    globalMapInstance.setView([lat, lng], 15, {
        animate: true,
        duration: 1
    });
    setTimeout(triggerSpiderfy, 1300);
}

function requestSpiderfyAtLocation(lat, lng, options) {
    if (!globalMarkerClusterGroup || typeof globalMarkerClusterGroup.zoomToShowLayer !== "function") return;
    var target = findMarkerAtLocation(lat, lng);
    if (!target) return;

    globalMarkerClusterGroup.zoomToShowLayer(target, function() {
        var targetLatLng = target.getLatLng();
        var parentCluster = target.__parent;
        if (!parentCluster || typeof parentCluster.spiderfy !== "function") {
            forceCenterOnLatLng(targetLatLng, options);
            return;
        }
        if (!globalMapInstance || !globalMapInstance.hasLayer(parentCluster)) {
            forceCenterOnLatLng(targetLatLng, options);
            return;
        }
        if (typeof window.setPendingSpiderfyFocusLatLng === "function") {
            window.setPendingSpiderfyFocusLatLng(targetLatLng);
        }
        parentCluster.spiderfy();
        forceCenterOnLatLng(targetLatLng, options);
    });
}

function findMarkerAtLocation(lat, lng) {
    if (!globalMarkerClusterGroup) return null;
    var targetLat = Number(lat);
    var targetLng = Number(lng);
    if (!isFinite(targetLat) || !isFinite(targetLng)) return null;

    var tolerance = 0.000001;
    var found = null;
    globalMarkerClusterGroup.eachLayer(function(layer) {
        if (found) return;
        if (!(layer instanceof L.Marker)) return;
        if (typeof layer.getAllChildMarkers === "function") return;
        var layerLatLng = layer.getLatLng();
        if (!layerLatLng) return;
        if (
            Math.abs(layerLatLng.lat - targetLat) <= tolerance &&
            Math.abs(layerLatLng.lng - targetLng) <= tolerance
        ) {
            found = layer;
        }
    });
    return found;
}

function findMarkerByActivityLogId(activityLogId) {
    if (!globalMarkerClusterGroup) return null;
    var targetId = parseInt(activityLogId, 10);
    if (!Number.isFinite(targetId) || targetId <= 0) return null;

    var found = null;
    globalMarkerClusterGroup.eachLayer(function(layer) {
        if (found) return;
        if (!(layer instanceof L.Marker)) return;
        if (typeof layer.getAllChildMarkers === "function") return;
        var markerActivityLogId = parseInt(layer.options.activityLogId || layer.options.activity_log_id, 10);
        if (markerActivityLogId === targetId) {
            found = layer;
        }
    });
    return found;
}

function openActivityLogMarker(activityLogId) {
    var target = findMarkerByActivityLogId(activityLogId);
    if (!target || !globalMarkerClusterGroup || typeof globalMarkerClusterGroup.zoomToShowLayer !== "function") {
        return false;
    }

    globalMarkerClusterGroup.zoomToShowLayer(target, function() {
        var latLng = target.getLatLng();
        forceCenterOnLatLng(latLng, { forceCenter: true });
        target.fire("click");
    });
    return true;
}

function openInitialActivityFromUrl() {
    if (window.__mapAppInitialActivityOpened) return false;
    var params = new URLSearchParams(window.location.search || "");
    if (!window.__mapAppInitialActivityLogId) {
        window.__mapAppInitialActivityLogId = params.get("activity_log_id") || "";
    }
    var activityLogId = window.__mapAppInitialActivityLogId;
    if (!activityLogId) return false;
    if (!openActivityLogMarker(activityLogId)) return false;
    window.__mapAppInitialActivityOpened = true;
    return true;
}

function forceCenterOnLatLng(latLng, options) {
    if (!globalMapInstance || !latLng) return;
    if (!options || !options.forceCenter) return;
    globalMapInstance.panTo(latLng, {
        animate: true,
        duration: 0.3
    });
}
