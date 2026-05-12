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

function forceCenterOnLatLng(latLng, options) {
    if (!globalMapInstance || !latLng) return;
    if (!options || !options.forceCenter) return;
    globalMapInstance.panTo(latLng, {
        animate: true,
        duration: 0.3
    });
}
