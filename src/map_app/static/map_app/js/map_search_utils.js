(function(global) {
    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function readSearchPanelState(storageKey) {
        try {
            return window.localStorage.getItem(storageKey) === "1";
        } catch (error) {
            return false;
        }
    }

    function writeSearchPanelState(storageKey, isOpen) {
        try {
            window.localStorage.setItem(storageKey, isOpen ? "1" : "0");
        } catch (error) {
            // Ignore storage errors.
        }
    }

    function replaceBrowserUrl(params) {
        var nextQuery = params.toString();
        var nextUrl = window.location.pathname + (nextQuery ? "?" + nextQuery : "") + window.location.hash;
        window.history.replaceState({}, "", nextUrl);
    }

    global.MapSearchUtils = {
        escapeHtml: escapeHtml,
        readSearchPanelState: readSearchPanelState,
        writeSearchPanelState: writeSearchPanelState,
        replaceBrowserUrl: replaceBrowserUrl,
    };
})(window);
