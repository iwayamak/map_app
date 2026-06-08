var MAX_MODAL_PAYLOAD_CACHE_SIZE = 50;
var modalPayloadCache = new Map();

function getCachedModalPayload(cacheKey) {
    if (!modalPayloadCache.has(cacheKey)) return null;
    var payload = modalPayloadCache.get(cacheKey);
    modalPayloadCache.delete(cacheKey);
    modalPayloadCache.set(cacheKey, payload);
    return payload;
}

function setCachedModalPayload(cacheKey, payload) {
    if (modalPayloadCache.has(cacheKey)) {
        modalPayloadCache.delete(cacheKey);
    }
    modalPayloadCache.set(cacheKey, payload);

    while (modalPayloadCache.size > MAX_MODAL_PAYLOAD_CACHE_SIZE) {
        var oldestKey = modalPayloadCache.keys().next().value;
        modalPayloadCache.delete(oldestKey);
    }
}

function getActivityModalApiUrl(activityId) {
    return "/api/activities/" + activityId + "/modal/";
}

function getLocationModalApiUrl(locationId) {
    return "/api/locations/" + locationId + "/modal/";
}

function fetchModalContent(markerIdentity) {
    var cacheKey = (markerIdentity.type || "activity_log") + ":" + String(markerIdentity.id || "");
    var cached = getCachedModalPayload(cacheKey);
    if (cached) return Promise.resolve(cached);
    var slowModalTimer = null;

    if (window.MapAppPageLoading && typeof window.MapAppPageLoading.show === "function") {
        slowModalTimer = setTimeout(function() {
            window.MapAppPageLoading.show({
                title: "詳細を読み込んでいます...",
                copy: "タップは受け付け済みです。そのままお待ちください。"
            });
        }, 500);
    }

    function clearSlowModalLoading() {
        if (slowModalTimer) {
            clearTimeout(slowModalTimer);
            slowModalTimer = null;
        }
        if (window.MapAppPageLoading && typeof window.MapAppPageLoading.hide === "function") {
            window.MapAppPageLoading.hide();
        }
    }

    var modalUrl = markerIdentity.type === "location"
        ? getLocationModalApiUrl(markerIdentity.id)
        : getActivityModalApiUrl(markerIdentity.id);

    return fetch(modalUrl, {
        method: "GET",
        headers: { "X-Requested-With": "XMLHttpRequest" }
    })
        .then(function(response) {
            if (!response.ok) throw new Error("Failed to fetch modal content");
            return response.json();
        })
        .then(function(payload) {
            var activity = payload && payload.activity;
            if (!activity) throw new Error("Invalid modal payload");
            setCachedModalPayload(cacheKey, activity);
            clearSlowModalLoading();
            return activity;
        })
        .catch(function(error) {
            clearSlowModalLoading();
            throw error;
        });
}
