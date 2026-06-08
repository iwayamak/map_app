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
                        "<span class='map-loading-piano-white-key'></span>" +
                        "<span class='map-loading-piano-white-key'></span>" +
                        "<span class='map-loading-piano-white-key'></span>" +
                        "<span class='map-loading-piano-white-key'></span>" +
                        "<span class='map-loading-piano-white-key'></span>" +
                        "<span class='map-loading-piano-white-key'></span>" +
                    "</span>" +
                    "<span class='map-loading-piano-black-keys' aria-hidden='true'>" +
                        "<span class='map-loading-piano-black-key is-csharp'></span>" +
                        "<span class='map-loading-piano-black-key is-dsharp'></span>" +
                        "<span class='map-loading-piano-black-key is-fsharp'></span>" +
                        "<span class='map-loading-piano-black-key is-gsharp'></span>" +
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
