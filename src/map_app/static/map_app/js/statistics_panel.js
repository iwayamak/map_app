(function(global) {
    var statisticsInitialized = false;

    function getDependencies() {
        if (!global.StatisticsStore || !global.StatisticsDomUi || !global.StatisticsChartUi) {
            return null;
        }
        return {
            store: global.StatisticsStore,
            domUi: global.StatisticsDomUi,
            chartUi: global.StatisticsChartUi,
        };
    }

    function renderStatistics(deps, payload) {
        if (!payload) return;
        deps.domUi.render(payload);
        deps.domUi.bindLocationEvents();
        deps.chartUi.render(payload);
    }

    function initStatisticsPanel() {
        var deps = getDependencies();
        if (!deps) return;
        var payload = deps.store.getPayload();
        if (!payload) return;

        renderStatistics(deps, payload);
        if (!statisticsInitialized) {
            statisticsInitialized = true;
        }
    }

    function initStatisticsPanelOnOpen() {
        var deps = getDependencies();
        if (!deps) return;
        deps.chartUi.ensureChartJsLoaded()
            .then(function() {
                initStatisticsPanel();
            })
            .catch(function(error) {
                console.error(error);
            });
    }

    function updateStatisticsPanelData(payload) {
        var deps = getDependencies();
        if (!deps || !payload || typeof payload !== "object") return;

        deps.store.setPayload(payload);
        deps.domUi.render(payload);
        deps.domUi.bindLocationEvents();

        if (deps.chartUi.isChartReady()) {
            deps.chartUi.render(payload);
        }
    }

    global.updateStatisticsPanelData = updateStatisticsPanelData;
    global.initStatisticsPanel = initStatisticsPanel;
    global.initStatisticsPanelOnOpen = initStatisticsPanelOnOpen;
    window.addEventListener("statistics:open", initStatisticsPanelOnOpen);
})(window);
