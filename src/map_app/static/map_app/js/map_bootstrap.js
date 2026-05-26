function waitForMapInstance(mapId, onReady) {
    var maxRetries = 20;
    var retryIntervalMs = 100;
    var retries = 0;

    function tryResolve() {
        var mapObj = window["map_" + mapId];
        if (typeof mapObj === "undefined") {
            retries += 1;
            if (retries < maxRetries) {
                setTimeout(tryResolve, retryIntervalMs);
            }
            return;
        }
        onReady(mapObj);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", tryResolve, { once: true });
        return;
    }
    tryResolve();
}

function findMarkerClusterGroup(mapObj) {
    var clusterGroup = null;
    if (!mapObj) return clusterGroup;

    mapObj.eachLayer(function(layer) {
        if (layer instanceof L.MarkerClusterGroup) {
            clusterGroup = layer;
        }
    });
    return clusterGroup;
}

function bindClusterMarkerEvents(clusterGroup) {
    clusterGroup.eachLayer(function(layer) {
        var isMarker = layer instanceof L.Marker;
        var isClusterMarker = typeof layer.getAllChildMarkers === "function";
        if (!isMarker || isClusterMarker) return;

        var activityLogId = resolveActivityLogId(layer);
        var locationId = resolveLocationId(layer);
        handleMarkerClick(layer, buildMarkerIdentity(activityLogId, locationId));
    });
}
