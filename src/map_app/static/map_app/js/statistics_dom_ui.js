(function(global) {
    var DEFAULT_MAP_TERMS = {
        use_record_items: true
    };

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function getMapTerms() {
        var node = document.getElementById("map-domain-terms");
        if (!node || !node.textContent) return DEFAULT_MAP_TERMS;
        try {
            var parsed = JSON.parse(node.textContent);
            return Object.assign({}, DEFAULT_MAP_TERMS, parsed || {});
        } catch (error) {
            return DEFAULT_MAP_TERMS;
        }
    }

    function bindLocationEvents() {
        document.querySelectorAll(".visit-item, .location-item").forEach(function(item) {
            if (item.dataset.statsBound === "1") return;
            item.dataset.statsBound = "1";
            item.addEventListener("click", function() {
                var lat = parseFloat(this.dataset.lat);
                var lng = parseFloat(this.dataset.lng);

                var statsPanel = document.getElementById("statistics-panel");
                if (statsPanel && statsPanel.style.opacity === "1" && typeof toggleStatistics === "function") {
                    toggleStatistics();
                }

                if (typeof zoomToLocation === "function") {
                    zoomToLocation(lat, lng);
                }
            });
        });
    }

    function renderRecentVisits(payload) {
        var list = document.getElementById("recent-visits-list");
        if (!list) return;
        var showVisitTitle = list.dataset.showVisitTitle !== "0";
        if (!getMapTerms().use_record_items) {
            showVisitTitle = false;
        }
        var visitTitleIcon = list.dataset.visitTitleIcon || "🎵";
        var visitTitleLabel = list.dataset.visitTitleLabel || "記録";

        var visits = [];
        if (payload && Array.isArray(payload.recent_visits)) {
            visits = payload.recent_visits;
        } else if (payload && Array.isArray(payload.recent_visits_data)) {
            // Backward compatibility for old payload key
            visits = payload.recent_visits_data;
        }
        if (!visits.length) {
            list.innerHTML = "<div class='visit-item-empty'>該当データがありません</div>";
            return;
        }

        list.innerHTML = visits.map(function(visit) {
            var titleHtml = "";
            if (showVisitTitle) {
                titleHtml =
                    "<div class='visit-title'>" +
                    escapeHtml(visitTitleIcon) + " " + escapeHtml(visitTitleLabel) +
                    (visit.title ? ": " + escapeHtml(visit.title) : "") +
                    "</div>";
            }
            return (
                "<button type='button' class='visit-item' data-lat='" + visit.latitude + "' data-lng='" + visit.longitude + "'>" +
                    "<div class='visit-name'>" + escapeHtml(visit.location_name) + "</div>" +
                    "<div class='visit-date'>📅 " + escapeHtml(visit.date) + "</div>" +
                    titleHtml +
                "</button>"
            );
        }).join("");
    }

    function renderTopLocations(payload) {
        var list = document.getElementById("top-locations-list");
        if (!list) return;

        var locations = [];
        if (payload && Array.isArray(payload.top_locations)) {
            locations = payload.top_locations;
        } else if (payload && Array.isArray(payload.top_locations_data)) {
            // Backward compatibility for old payload key
            locations = payload.top_locations_data;
        }
        if (!locations.length) {
            list.innerHTML = "<div class='location-item-empty'>該当データがありません</div>";
            return;
        }

        list.innerHTML = locations.map(function(location, index) {
            var rank = index + 1;
            var rankHtml = "";
            if (rank === 1) rankHtml = "<span class='location-rank location-rank-medal' aria-label='1位'>🥇</span>";
            else if (rank === 2) rankHtml = "<span class='location-rank location-rank-medal' aria-label='2位'>🥈</span>";
            else if (rank === 3) rankHtml = "<span class='location-rank location-rank-medal' aria-label='3位'>🥉</span>";
            else rankHtml = "<span class='location-rank location-rank-number' aria-label='" + rank + "位'>" + rank + "</span>";

            return (
                "<button type='button' class='location-item' data-lat='" + location.latitude + "' data-lng='" + location.longitude + "'>" +
                    "<span class='location-main'>" +
                        rankHtml +
                        "<span class='location-name'>" + escapeHtml(location.name) + "</span>" +
                    "</span>" +
                    "<span class='location-badge'>" + escapeHtml(location.count) + "回</span>" +
                "</button>"
            );
        }).join("");
    }

    function render(payload) {
        renderRecentVisits(payload);
        renderTopLocations(payload);
    }

    global.StatisticsDomUi = {
        bindLocationEvents: bindLocationEvents,
        render: render,
    };
})(window);
