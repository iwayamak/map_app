(function() {
    function applyObjectToolsResponsiveWidth() {
        var isMobile = window.matchMedia("(max-width: 768px)").matches;
        var tools = document.querySelector(".change-list .object-tools");
        if (!tools) return;

        var items = tools.querySelectorAll("li");
        items.forEach(function(item) {
            if (!isMobile) {
                item.style.removeProperty("flex");
                return;
            }

            var link = item.querySelector("a");
            if (!link) return;
            var text = (link.textContent || "").trim();
            var length = Array.from(text).length;
            var weight = Math.max(8, length + 2);
            item.style.flex = weight + " 1 0";
        });
    }

    document.addEventListener("DOMContentLoaded", applyObjectToolsResponsiveWidth);
    window.addEventListener("resize", applyObjectToolsResponsiveWidth);
})();
