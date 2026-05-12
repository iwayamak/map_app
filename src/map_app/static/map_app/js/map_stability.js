var mapInvalidateRafId = null;
var mapInvalidateTimerId = null;

function invalidateMapSizeSafely(mapObj) {
    if (!mapObj || typeof mapObj.invalidateSize !== "function") return;
    mapObj.invalidateSize({ pan: false });
}

function requestMapInvalidate(options) {
    var opts = options || {};
    var mapObj = globalMapInstance;
    if (!mapObj) return;

    if (mapInvalidateRafId) {
        cancelAnimationFrame(mapInvalidateRafId);
    }
    mapInvalidateRafId = requestAnimationFrame(function() {
        invalidateMapSizeSafely(mapObj);
        mapInvalidateRafId = null;
    });

    if (opts.delayed) {
        if (mapInvalidateTimerId) {
            clearTimeout(mapInvalidateTimerId);
        }
        mapInvalidateTimerId = setTimeout(function() {
            invalidateMapSizeSafely(mapObj);
            mapInvalidateTimerId = null;
        }, 260);
    }
}

function bindMapStabilityGuards(mapObj, clusterGroup) {
    if (!mapObj || mapObj._stabilityGuardsBound) return;

    var onViewportChanged = function() {
        requestMapInvalidate({ delayed: true });
    };
    window.addEventListener("resize", onViewportChanged);
    window.addEventListener("orientationchange", onViewportChanged);

    if (window.visualViewport) {
        window.visualViewport.addEventListener("resize", onViewportChanged);
    }

    mapObj.eachLayer(function(layer) {
        if (!(layer instanceof L.TileLayer) || layer._tileErrorGuardBound) return;
        layer.on("tileerror", function() {
            requestMapInvalidate({ delayed: true });
        });
        layer._tileErrorGuardBound = true;
    });

    clusterGroup.on("spiderfied", function() {
        requestMapInvalidate({ delayed: true });
    });

    mapObj._stabilityGuardsBound = true;
}

window.requestMapInvalidate = requestMapInvalidate;
