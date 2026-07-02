var DEFAULT_MAP_CENTER = [35.686, 138.360];
var DEFAULT_MAP_ZOOM = 5;
var globalMapInstance = null;
var globalMarkerClusterGroup = null;

function bindMarkerEvents(mapId) {
    waitForMapInstance(mapId, function(mapObj) {
        globalMapInstance = mapObj;
        var clusterGroup = findMarkerClusterGroup(mapObj);

        if (!clusterGroup) return;
        globalMarkerClusterGroup = clusterGroup;
        tuneMobileSpiderfyDistance(clusterGroup);
        ensureResetZoomControl(mapObj);
        bindClusterMarkerEvents(clusterGroup);
        keepSpiderfyCenterOnViewportCenter(mapObj, clusterGroup);
        bindMapStabilityGuards(mapObj, clusterGroup);
        if (typeof openInitialActivityFromUrl === "function") {
            setTimeout(openInitialActivityFromUrl, 150);
        }
    });
}
