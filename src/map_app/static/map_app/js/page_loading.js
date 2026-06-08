(function(global) {
    var overlay = null;
    var escalationTimers = [];
    var loading = false;

    function ensureOverlay() {
        if (overlay) return overlay;
        overlay = document.createElement("div");
        overlay.id = "map-page-loading";
        overlay.className = "map-page-loading";
        overlay.setAttribute("role", "status");
        overlay.setAttribute("aria-live", "polite");
        overlay.innerHTML =
            "<div class='map-page-loading-card'>" +
                (global.MapAppLoadingSpinner ? global.MapAppLoadingSpinner.render("map-page-loading-spinner") : "<div class='map-page-loading-spinner' aria-hidden='true'><span class='map-loading-ring'></span></div>") +
                "<p class='map-page-loading-title'>読み込み中</p>" +
            "</div>";
        if (global.MapAppLoadingSpinner) global.MapAppLoadingSpinner.applyToNode(overlay);
        document.body.appendChild(overlay);
        return overlay;
    }

    function setText(title) {
        var node = ensureOverlay();
        var titleNode = node.querySelector(".map-page-loading-title");
        if (titleNode && title) titleNode.textContent = title;
    }

    function clearEscalationTimers() {
        escalationTimers.forEach(function(timerId) {
            clearTimeout(timerId);
        });
        escalationTimers = [];
    }

    function show(options) {
        var nextOptions = options || {};
        loading = true;
        setText(nextOptions.title || "読み込み中");
        ensureOverlay().classList.add("is-visible");
        document.documentElement.classList.add("map-page-loading-active");
    }

    function hide() {
        loading = false;
        clearEscalationTimers();
        document.documentElement.classList.remove("map-page-loading-active");
        if (overlay) overlay.classList.remove("is-visible");
    }

    function navigate(url, options) {
        show(options || { title: "読み込み中" });
        var delayMs = global.MapAppLoadingSpinner && typeof global.MapAppLoadingSpinner.getNavigationDelay === "function"
            ? global.MapAppLoadingSpinner.getNavigationDelay()
            : 90;
        requestAnimationFrame(function() {
            setTimeout(function() {
                window.location.assign(url);
            }, delayMs);
        });
    }

    function isSkippableLink(link, event) {
        if (!link || !link.href) return true;
        if (link.dataset.noPageLoading === "1") return true;
        if (link.target && link.target !== "_self") return true;
        if (link.hasAttribute("download")) return true;
        if (event && (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0)) return true;

        var href = link.getAttribute("href") || "";
        if (!href || href.charAt(0) === "#" || href.indexOf("javascript:") === 0 || href.indexOf("mailto:") === 0 || href.indexOf("tel:") === 0) return true;

        try {
            var url = new URL(link.href, window.location.href);
            if (url.origin !== window.location.origin) return true;
            if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) return true;
        } catch (error) {
            return true;
        }
        return false;
    }

    function bindPageTransitions() {
        document.addEventListener("click", function(event) {
            var link = event.target.closest && event.target.closest("a[href]");
            if (isSkippableLink(link, event)) return;
            if (loading) {
                event.preventDefault();
                return;
            }
            event.preventDefault();
            link.classList.add("is-page-loading-source");
            navigate(link.href, { title: "読み込み中" });
        }, true);

        document.addEventListener("submit", function(event) {
            var form = event.target;
            if (!form || form.dataset.noPageLoading === "1") return;
            if (form.id === "map-search-form") return;
            if (form.dataset.pageLoadingSubmitting === "1") {
                event.preventDefault();
                return;
            }
            form.dataset.pageLoadingSubmitting = "1";
            show({ title: "読み込み中" });
        }, true);

        window.addEventListener("pageshow", hide);
        window.addEventListener("pagehide", clearEscalationTimers);
    }

    global.MapAppPageLoading = {
        bindPageTransitions: bindPageTransitions,
        show: show,
        hide: hide,
        navigate: navigate,
        isLoading: function() { return loading; }
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bindPageTransitions, { once: true });
    } else {
        bindPageTransitions();
    }
})(window);
