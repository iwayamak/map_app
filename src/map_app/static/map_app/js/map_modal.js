document.addEventListener("keydown", function(event) {
    if (event.key === "Escape") {
        closeDetailModal();
        closeImageModal();
    }
});

document.addEventListener("click", function(event) {
    if (event.target.id === "detailModal") closeDetailModal();
    if (event.target.id === "imageModal") closeImageModal();

    var tagChip = event.target.closest(".activity-modal-tag-chip[data-tag-name], .performance-modal-tag-chip[data-tag-name]");
    if (!tagChip) return;

    event.preventDefault();
    event.stopPropagation();

    var selectedTag = tagChip.getAttribute("data-tag-name");
    var actions = window.MapSearchActions;
    if (!selectedTag || !actions || typeof actions.applyTagFilterFromModal !== "function") return;

    closeDetailModal();
    actions.applyTagFilterFromModal(selectedTag);
});

function handleMarkerClick(marker, markerIdentity) {
    marker.off("click");
    marker.on("click", function(e) {
        L.DomEvent.stopPropagation(e);
        if (!markerIdentity) {
            return;
        }

        showDetailModal(buildLoadingModalHtml());
        fetchModalContent(markerIdentity)
            .then(function(performance) {
                showDetailModal(renderPerformanceModal(performance));
            })
            .catch(function() {
                showDetailModal(buildErrorModalHtml());
            });
    });
}

function buildLiveMarkerTooltipHtml(markerPayload) {
    var activityLogId = markerPayload.activity_log_id || markerPayload.performance_id || "";
    return (
        "<span data-activity-log-id='" + escapeHtml(activityLogId) + "' data-performance-id='" + escapeHtml(activityLogId) + "'>" +
            escapeHtml(markerPayload.location_name || "") + " / " + escapeHtml(markerPayload.date || "") +
        "</span>"
    );
}

function buildLiveMarkerIconHtml(iconColor) {
    var safeColor = escapeHtml(iconColor || "#3b82f6");
    return (
        "<div style='position: relative;'>" +
            "<div style='width: 35px; height: 45px; background: " + safeColor + "; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 3px solid white; box-shadow: 0 3px 8px rgba(0,0,0,0.3);'></div>" +
            "<div style='position: absolute; top: 8px; left: 8px; width: 19px; height: 19px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;'>" +
                "<i class='fa fa-music' style='color: " + safeColor + "; font-size: 10px; transform: rotate(45deg);'></i>" +
            "</div>" +
        "</div>"
    );
}

function replaceMapMarkers(markers) {
    if (!globalMarkerClusterGroup || !Array.isArray(markers)) return false;

    globalMarkerClusterGroup.clearLayers();
    markers.forEach(function(item) {
        var lat = Number(item.lat);
        var lng = Number(item.lng);
        var activityLogId = parseInt(item.activity_log_id || item.performance_id, 10);
        var locationId = parseInt(item.location_id, 10);
        if (Number.isNaN(lat) || Number.isNaN(lng) || Number.isNaN(activityLogId) || Number.isNaN(locationId)) return;

        var marker = L.marker(
            [lat, lng],
            {
                icon: L.divIcon({ html: buildLiveMarkerIconHtml(item.icon_color), className: "" }),
                activityLogId: activityLogId,
                performanceId: activityLogId,
                locationId: locationId
            }
        );
        marker.bindTooltip(buildLiveMarkerTooltipHtml(item), { direction: "top" });
        handleMarkerClick(marker, buildMarkerIdentity(activityLogId, locationId));
        globalMarkerClusterGroup.addLayer(marker);
    });
    return true;
}
