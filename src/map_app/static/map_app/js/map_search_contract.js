(function(global) {
    var MARKER_FIELDS = [
        "activity_log_id",
        "performance_id",
        "location_id",
        "location_name",
        "date",
        "lat",
        "lng",
        "icon_color",
    ];

    var SUMMARY_FIELDS = [
        "total_locations",
        "total_activity_logs",
        "total_performances",
        "marker_count",
        "tagged_locations",
        "new_count",
        "revisit_count",
    ];
    var STATISTICS_FIELDS = [
        "month_labels",
        "month_values",
        "recent_visits",
        "top_locations",
    ];
    var RECENT_VISIT_FIELDS = [
        "location_name",
        "date",
        "title",
        "latitude",
        "longitude",
    ];
    var TOP_LOCATION_FIELDS = [
        "name",
        "count",
        "latitude",
        "longitude",
    ];

    var MAP_SEARCH_RESPONSE_SCHEMA = {
        type: "object",
        required: ["markers", "summary", "statistics"],
        additionalProperties: false,
        properties: {
            markers: {
                type: "array",
                items: {
                    type: "object",
                    required: MARKER_FIELDS.slice(),
                    additionalProperties: false,
                    properties: {
                        activity_log_id: { type: "integer" },
                        performance_id: { type: "integer" },
                        location_id: { type: "integer" },
                        location_name: { type: "string" },
                        date: { type: "string" },
                        lat: { type: "number" },
                        lng: { type: "number" },
                        icon_color: { type: "string" },
                    },
                },
            },
            summary: {
                type: "object",
                required: SUMMARY_FIELDS.slice(),
                additionalProperties: false,
                properties: {
                    total_locations: { type: "integer" },
                    total_activity_logs: { type: "integer" },
                    total_performances: { type: "integer" },
                    marker_count: { type: "integer" },
                    tagged_locations: { type: "integer" },
                    new_count: { type: "integer" },
                    revisit_count: { type: "integer" },
                },
            },
            statistics: {
                type: "object",
                required: STATISTICS_FIELDS.slice(),
                additionalProperties: false,
                properties: {
                    month_labels: { type: "array", items: { type: "string" } },
                    month_values: { type: "array", items: { type: "integer" } },
                    recent_visits: {
                        type: "array",
                        items: {
                            type: "object",
                            required: RECENT_VISIT_FIELDS.slice(),
                            additionalProperties: false,
                            properties: {
                                location_name: { type: "string" },
                                date: { type: "string" },
                                title: { type: "string" },
                                latitude: { type: "number" },
                                longitude: { type: "number" },
                            },
                        },
                    },
                    top_locations: {
                        type: "array",
                        items: {
                            type: "object",
                            required: TOP_LOCATION_FIELDS.slice(),
                            additionalProperties: false,
                            properties: {
                                name: { type: "string" },
                                count: { type: "integer" },
                                latitude: { type: "number" },
                                longitude: { type: "number" },
                            },
                        },
                    },
                },
            },
        },
    };

    function hasExactlyKeys(target, expectedKeys) {
        var keys = Object.keys(target).sort();
        var sortedExpected = expectedKeys.slice().sort();
        if (keys.length !== sortedExpected.length) return false;
        for (var i = 0; i < keys.length; i += 1) {
            if (keys[i] !== sortedExpected[i]) return false;
        }
        return true;
    }

    function assertInteger(value, fieldName) {
        if (!Number.isInteger(value)) {
            throw new Error("Invalid map search payload: '" + fieldName + "' must be integer.");
        }
    }

    function assertFiniteNumber(value, fieldName) {
        if (typeof value !== "number" || !Number.isFinite(value)) {
            throw new Error("Invalid map search payload: '" + fieldName + "' must be number.");
        }
    }

    function assertString(value, fieldName) {
        if (typeof value !== "string") {
            throw new Error("Invalid map search payload: '" + fieldName + "' must be string.");
        }
    }

    function validateMapSearchPayload(payload) {
        if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
            throw new Error("Invalid map search payload: root must be object.");
        }
        if (!hasExactlyKeys(payload, MAP_SEARCH_RESPONSE_SCHEMA.required)) {
            throw new Error("Invalid map search payload: root keys mismatch.");
        }
        if (!Array.isArray(payload.markers)) {
            throw new Error("Invalid map search payload: 'markers' must be array.");
        }
        payload.markers.forEach(function(marker, index) {
            if (!marker || typeof marker !== "object" || Array.isArray(marker)) {
                throw new Error("Invalid map search payload: marker[" + index + "] must be object.");
            }
            if (!hasExactlyKeys(marker, MARKER_FIELDS)) {
                throw new Error("Invalid map search payload: marker keys mismatch.");
            }
            assertInteger(marker.activity_log_id, "activity_log_id");
            assertInteger(marker.performance_id, "performance_id");
            assertInteger(marker.location_id, "location_id");
            assertString(marker.location_name, "location_name");
            assertString(marker.date, "date");
            assertFiniteNumber(marker.lat, "lat");
            assertFiniteNumber(marker.lng, "lng");
            assertString(marker.icon_color, "icon_color");
        });

        var summary = payload.summary;
        if (!summary || typeof summary !== "object" || Array.isArray(summary)) {
            throw new Error("Invalid map search payload: 'summary' must be object.");
        }
        if (!hasExactlyKeys(summary, SUMMARY_FIELDS)) {
            throw new Error("Invalid map search payload: summary keys mismatch.");
        }
        assertInteger(summary.total_locations, "total_locations");
        assertInteger(summary.total_activity_logs, "total_activity_logs");
        assertInteger(summary.total_performances, "total_performances");
        assertInteger(summary.marker_count, "marker_count");
        assertInteger(summary.tagged_locations, "tagged_locations");
        assertInteger(summary.new_count, "new_count");
        assertInteger(summary.revisit_count, "revisit_count");

        var statistics = payload.statistics;
        if (!statistics || typeof statistics !== "object" || Array.isArray(statistics)) {
            throw new Error("Invalid map search payload: 'statistics' must be object.");
        }
        if (!hasExactlyKeys(statistics, STATISTICS_FIELDS)) {
            throw new Error("Invalid map search payload: statistics keys mismatch.");
        }

        if (!Array.isArray(statistics.month_labels)) {
            throw new Error("Invalid map search payload: 'month_labels' must be array.");
        }
        statistics.month_labels.forEach(function(label) {
            assertString(label, "month_labels");
        });

        if (!Array.isArray(statistics.month_values)) {
            throw new Error("Invalid map search payload: 'month_values' must be array.");
        }
        statistics.month_values.forEach(function(value) {
            assertInteger(value, "month_values");
        });

        if (!Array.isArray(statistics.recent_visits)) {
            throw new Error("Invalid map search payload: 'recent_visits' must be array.");
        }
        statistics.recent_visits.forEach(function(visit, index) {
            if (!visit || typeof visit !== "object" || Array.isArray(visit)) {
                throw new Error("Invalid map search payload: recent_visits[" + index + "] must be object.");
            }
            if (!hasExactlyKeys(visit, RECENT_VISIT_FIELDS)) {
                throw new Error("Invalid map search payload: recent visit keys mismatch.");
            }
            assertString(visit.location_name, "location_name");
            assertString(visit.date, "date");
            assertString(visit.title, "title");
            assertFiniteNumber(visit.latitude, "latitude");
            assertFiniteNumber(visit.longitude, "longitude");
        });

        if (!Array.isArray(statistics.top_locations)) {
            throw new Error("Invalid map search payload: 'top_locations' must be array.");
        }
        statistics.top_locations.forEach(function(item, index) {
            if (!item || typeof item !== "object" || Array.isArray(item)) {
                throw new Error("Invalid map search payload: top_locations[" + index + "] must be object.");
            }
            if (!hasExactlyKeys(item, TOP_LOCATION_FIELDS)) {
                throw new Error("Invalid map search payload: top location keys mismatch.");
            }
            assertString(item.name, "name");
            assertInteger(item.count, "count");
            assertFiniteNumber(item.latitude, "latitude");
            assertFiniteNumber(item.longitude, "longitude");
        });
    }

    global.MapSearchContract = {
        MAP_SEARCH_RESPONSE_SCHEMA: MAP_SEARCH_RESPONSE_SCHEMA,
        MARKER_FIELDS: MARKER_FIELDS,
        SUMMARY_FIELDS: SUMMARY_FIELDS,
        validateMapSearchPayload: validateMapSearchPayload,
    };
})(window);
