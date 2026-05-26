(function(global) {
    function createSummaryUi(elements) {
        function apply(summary) {
            if (!summary || typeof summary !== "object") return;
            var totalActivityLogs = summary.total_activity_logs || 0;
            if (elements.summaryTotalLocations) elements.summaryTotalLocations.textContent = String(summary.total_locations || 0);
            if (elements.summaryTaggedLocations) elements.summaryTaggedLocations.textContent = String(summary.tagged_locations || 0);
            if (elements.summaryTotalActivityLogs) elements.summaryTotalActivityLogs.textContent = String(totalActivityLogs);
            if (elements.liveLocationsCount) elements.liveLocationsCount.textContent = String(summary.total_locations || 0);
            if (elements.liveActivityLogsCount) elements.liveActivityLogsCount.textContent = String(summary.marker_count || 0);
        }

        function syncFromCurrentSummaryDom() {
            if (elements.liveLocationsCount && elements.summaryTotalLocations) {
                elements.liveLocationsCount.textContent = elements.summaryTotalLocations.textContent || "0";
            }
            var summaryActivityLogCount = elements.summaryTotalActivityLogs;
            if (elements.liveActivityLogsCount && summaryActivityLogCount) {
                elements.liveActivityLogsCount.textContent = summaryActivityLogCount.textContent || "0";
            }
        }

        return {
            apply: apply,
            syncFromCurrentSummaryDom: syncFromCurrentSummaryDom,
        };
    }

    global.MapSearchSummaryUi = {
        create: createSummaryUi,
    };
})(window);
