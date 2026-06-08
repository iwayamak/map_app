(function(global) {
    var VALID_STYLES = {
        simple_ring: true,
        piano_keys: true,
    };

    function normalizeStyle(style) {
        var normalized = String(style || "").trim().toLowerCase();
        if (VALID_STYLES[normalized]) return normalized;
        return "simple_ring";
    }

    function getStyle() {
        var rootStyle = document.documentElement && document.documentElement.dataset
            ? document.documentElement.dataset.loadingStyle
            : "";
        var bodyStyle = document.body && document.body.dataset
            ? document.body.dataset.loadingStyle
            : "";
        return normalizeStyle(rootStyle || bodyStyle);
    }

    function renderInner(style) {
        if (style === "piano_keys") {
            return (
                "<span class='map-loading-piano-keys'>" +
                    "<span class='map-loading-piano-white-keys'>" +
                        "<span class='map-loading-piano-white-key is-key-1'></span>" +
                        "<span class='map-loading-piano-white-key is-key-2'></span>" +
                        "<span class='map-loading-piano-white-key is-key-3'></span>" +
                        "<span class='map-loading-piano-white-key is-key-4'></span>" +
                        "<span class='map-loading-piano-white-key is-key-5'></span>" +
                        "<span class='map-loading-piano-white-key is-key-6'></span>" +
                    "</span>" +
                    "<span class='map-loading-piano-black-keys' aria-hidden='true'>" +
                        "<span class='map-loading-piano-black-key is-csharp is-key-1'></span>" +
                        "<span class='map-loading-piano-black-key is-dsharp is-key-2'></span>" +
                        "<span class='map-loading-piano-black-key is-fsharp is-key-4'></span>" +
                        "<span class='map-loading-piano-black-key is-gsharp is-key-5'></span>" +
                    "</span>" +
                "</span>"
            );
        }
        return "<span class='map-loading-ring'></span>";
    }

    function render(className) {
        var style = getStyle();
        return (
            "<div class='" + className + "' data-loading-style='" + style + "' aria-hidden='true'>" +
                renderInner(style) +
            "</div>"
        );
    }

    function applyToNode(node) {
        if (!node) return node;
        node.setAttribute("data-loading-style", getStyle());
        return node;
    }

    global.MapAppLoadingSpinner = {
        getStyle: getStyle,
        render: render,
        applyToNode: applyToNode,
    };
})(window);
