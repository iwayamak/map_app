function ensureResetZoomControl(mapObj) {
    if (!mapObj || typeof L === "undefined" || !L.Control) return;
    if (mapObj._resetZoomControlAdded) return;

    var ResetZoomControl = L.Control.extend({
        options: {
            position: "topleft",
        },
        onAdd: function(map) {
            var container = L.DomUtil.create("div", "leaflet-bar leaflet-control leaflet-control-resetzoom");
            var button = L.DomUtil.create("a", "leaflet-control-resetzoom-button", container);
            button.href = "#";
            button.title = "デフォルト位置と縮尺に戻す";
            button.setAttribute("aria-label", "デフォルト位置と縮尺に戻す");
            button.innerHTML = "⌂";

            L.DomEvent.disableClickPropagation(container);
            L.DomEvent.on(button, "click", L.DomEvent.stop)
                .on(button, "click", function() {
                    map.setView(DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM, { animate: true });
                });
            return container;
        }
    });

    mapObj.addControl(new ResetZoomControl());
    mapObj._resetZoomControlAdded = true;
}

function resetMapViewToDefault() {
    if (!globalMapInstance) return;
    globalMapInstance.setView(DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM, {
        animate: true,
        duration: 0.6
    });
}
