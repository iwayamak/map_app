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
                "<div class='map-page-loading-spinner' aria-hidden='true'></div>" +
                "<p class='map-page-loading-title'>読み込み中...</p>" +
                "<p class='map-page-loading-copy'>そのままお待ちください。</p>" +
            "</div>";
        document.body.appendChild(overlay);
        return overlay;
    }

    function setText(title, copy) {
        var node = ensureOverlay();
        var titleNode = node.querySelector(".map-page-loading-title");
        var copyNode = node.querySelector(".map-page-loading-copy");
        if (titleNode && title) titleNode.textContent = title;
        if (copyNode && copy) copyNode.textContent = copy;
    }

    function clearEscalationTimers() {
        escalationTimers.forEach(function(timerId) {
            clearTimeout(timerId);
        });
        escalationTimers = [];
    }

    function scheduleEscalation(messages) {
        clearEscalationTimers();
        (messages || []).forEach(function(item) {
            escalationTimers.push(setTimeout(function() {
                setText(item.title, item.copy);
            }, item.delayMs));
        });
    }

    function show(options) {
        var nextOptions = options || {};
        loading = true;
        setText(nextOptions.title || "読み込み中...", nextOptions.copy || "そのままお待ちください。");
        ensureOverlay().classList.add("is-visible");
        document.documentElement.classList.add("map-page-loading-active");
        scheduleEscalation(nextOptions.escalationMessages || [
            { delayMs: 1500, title: "サーバー処理中です...", copy: "通信に時間がかかっています。再度タップせずお待ちください。" },
            { delayMs: 5000, title: "もう少しお待ちください", copy: "処理は継続中です。連続タップは不要です。" }
        ]);
    }

    function hide() {
        loading = false;
        clearEscalationTimers();
        document.documentElement.classList.remove("map-page-loading-active");
        if (overlay) overlay.classList.remove("is-visible");
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
            link.classList.add("is-page-loading-source");
            show({ title: "ページを開いています...", copy: "タップは受け付け済みです。そのままお待ちください。" });
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
            show({ title: "送信中です...", copy: "処理が完了するまで再送信せずお待ちください。" });
        }, true);

        window.addEventListener("pageshow", hide);
        window.addEventListener("pagehide", clearEscalationTimers);
    }

    global.MapAppPageLoading = {
        bindPageTransitions: bindPageTransitions,
        show: show,
        hide: hide,
        isLoading: function() { return loading; }
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bindPageTransitions, { once: true });
    } else {
        bindPageTransitions();
    }
})(window);
