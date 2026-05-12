(function(global) {
    function getPayload() {
        var element = document.getElementById("statistics-data");
        if (!element || !element.textContent) return null;

        try {
            return JSON.parse(element.textContent);
        } catch (error) {
            return null;
        }
    }

    function setPayload(payload) {
        if (!payload || typeof payload !== "object") return;
        var element = document.getElementById("statistics-data");
        if (!element) return;
        element.textContent = JSON.stringify(payload);
    }

    global.StatisticsStore = {
        getPayload: getPayload,
        setPayload: setPayload,
    };
})(window);
