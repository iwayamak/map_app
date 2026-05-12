(function(global) {
    var chartJsLoadPromise = null;
    var chartJsUrl = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js";
    var monthlyChartInstance = null;
    var topLocationsChartInstance = null;

    function getTopLocationsChartHeight() {
        if (window.innerWidth <= 480) return 360;
        if (window.innerWidth <= 768) return 390;
        return 430;
    }

    function applyTopLocationsChartHeight(canvas, height) {
        if (!canvas) return;
        var wrap = canvas.parentElement;
        if (wrap) {
            wrap.style.setProperty("height", height + "px", "important");
            wrap.style.setProperty("min-height", height + "px", "important");
            wrap.style.setProperty("max-height", height + "px", "important");
        }
        canvas.style.setProperty("height", height + "px", "important");
        canvas.style.setProperty("min-height", height + "px", "important");
        canvas.style.setProperty("max-height", height + "px", "important");
        canvas.height = height;
    }

    function getTopLocationsAnimationDuration() {
        return window.innerWidth <= 768 ? 0 : 180;
    }

    function buildTopLocationsColors(values) {
        return values.map(function(_, index) {
            if (index === 0) return "rgba(239, 68, 68, 0.82)";
            if (index === 1) return "rgba(251, 146, 60, 0.82)";
            if (index === 2) return "rgba(251, 191, 36, 0.82)";
            var alpha = Math.max(0.25, 0.8 - ((index - 3) * 0.03));
            return "rgba(59, 130, 246, " + alpha.toFixed(2) + ")";
        });
    }

    function buildTopLocationsBorderColors(values) {
        return values.map(function(_, index) {
            if (index === 0) return "rgba(239, 68, 68, 1)";
            if (index === 1) return "rgba(251, 146, 60, 1)";
            if (index === 2) return "rgba(251, 191, 36, 1)";
            return "rgba(59, 130, 246, 1)";
        });
    }

    function createMonthlyChart(payload) {
        var monthlyCanvas = document.getElementById("monthlyChart");
        if (!monthlyCanvas || typeof Chart === "undefined") return;

        var monthlyCtx = monthlyCanvas.getContext("2d");
        if (monthlyChartInstance) {
            monthlyChartInstance.destroy();
        }
        monthlyChartInstance = new Chart(monthlyCtx, {
            type: "line",
            data: {
                labels: payload.month_labels || [],
                datasets: [
                    {
                        label: "訪問回数",
                        data: payload.month_values || [],
                        borderColor: "#667eea",
                        backgroundColor: "rgba(102, 126, 234, 0.1)",
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: "#667eea",
                        pointBorderColor: "#fff",
                        pointBorderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "rgba(0, 0, 0, 0.8)",
                        padding: 12,
                        borderRadius: 8,
                        titleFont: { size: 14 },
                        bodyFont: { size: 13 },
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, font: { size: 11 } },
                        grid: { color: "rgba(0, 0, 0, 0.05)" },
                    },
                    x: {
                        ticks: {
                            font: { size: 10 },
                            maxRotation: 90,
                            minRotation: 45,
                            autoSkip: true,
                            maxTicksLimit: 12,
                        },
                        grid: { display: false },
                    },
                },
            },
        });
    }

    function createTopLocationsChart(payload) {
        var topLocationsCanvas = document.getElementById("topLocationsChart");
        if (!topLocationsCanvas || typeof Chart === "undefined") return;

        var locations = payload.top_locations || [];
        var labels = locations.map(function(loc) { return loc.name; });
        var values = locations.map(function(loc) { return loc.count; });
        var topLocationsCtx = topLocationsCanvas.getContext("2d");
        applyTopLocationsChartHeight(topLocationsCanvas, getTopLocationsChartHeight());
        var animationDuration = getTopLocationsAnimationDuration();
        if (topLocationsChartInstance) {
            topLocationsChartInstance.destroy();
        }
        var colors = buildTopLocationsColors(values);
        var borderColors = buildTopLocationsBorderColors(values);

        topLocationsChartInstance = new Chart(topLocationsCtx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "訪問回数",
                        data: values,
                        backgroundColor: colors,
                        borderColor: borderColors,
                        borderWidth: 2,
                        borderRadius: 6,
                        maxBarThickness: 14,
                        categoryPercentage: 0.8,
                        barPercentage: 0.9,
                    },
                ],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: animationDuration,
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "rgba(0, 0, 0, 0.8)",
                        padding: 12,
                        borderRadius: 8,
                        titleFont: { size: 14 },
                        bodyFont: { size: 13 },
                        callbacks: {
                            label: function(context) {
                                return "訪問回数: " + context.parsed.x + "回";
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, font: { size: 11 } },
                        grid: { color: "rgba(0, 0, 0, 0.05)" },
                    },
                    y: {
                        ticks: {
                            autoSkip: false,
                            font: { size: 10 },
                            callback: function(value) {
                                var label = this.getLabelForValue(value) || "";
                                return label.length > 14 ? (label.slice(0, 14) + "…") : label;
                            },
                        },
                        grid: { display: false },
                    },
                },
            },
        });
    }

    function ensureChartJsLoaded() {
        if (typeof Chart !== "undefined") {
            return Promise.resolve();
        }
        if (chartJsLoadPromise) {
            return chartJsLoadPromise;
        }

        chartJsLoadPromise = new Promise(function(resolve, reject) {
            var script = document.createElement("script");
            script.src = chartJsUrl;
            script.async = true;
            script.onload = function() {
                resolve();
            };
            script.onerror = function() {
                reject(new Error("Failed to load Chart.js"));
            };
            document.head.appendChild(script);
        });

        return chartJsLoadPromise;
    }

    function isChartReady() {
        return typeof Chart !== "undefined";
    }

    function render(payload) {
        if (!payload) return;
        createMonthlyChart(payload);
        createTopLocationsChart(payload);
    }

    global.StatisticsChartUi = {
        ensureChartJsLoaded: ensureChartJsLoaded,
        isChartReady: isChartReady,
        render: render,
    };
})(window);
