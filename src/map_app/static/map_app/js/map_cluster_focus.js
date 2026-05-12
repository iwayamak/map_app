var pendingSpiderfyFocusLatLng = null;

function keepSpiderfyCenterOnViewportCenter(mapObj, clusterGroup) {
    if (!mapObj || !clusterGroup) return;
    if (clusterGroup._spiderfyCenterBindingAdded) return;

    clusterGroup.on("spiderfied", function(event) {
        var cluster = event && event.cluster;
        if (!cluster || typeof cluster.getLatLng !== "function") return;
        var targetLatLng = pendingSpiderfyFocusLatLng || cluster.getLatLng();
        pendingSpiderfyFocusLatLng = null;
        var centerPoint = mapObj.latLngToContainerPoint(mapObj.getCenter());
        var targetPoint = mapObj.latLngToContainerPoint(targetLatLng);
        var distancePx = centerPoint.distanceTo(targetPoint);

        if (distancePx < 32) return;

        mapObj.panTo(targetLatLng, {
            animate: true,
            duration: 0.4,
            easeLinearity: 0.25
        });
    });

    clusterGroup._spiderfyCenterBindingAdded = true;
}

function setPendingSpiderfyFocusLatLng(latLng) {
    pendingSpiderfyFocusLatLng = latLng || null;
}

window.setPendingSpiderfyFocusLatLng = setPendingSpiderfyFocusLatLng;
