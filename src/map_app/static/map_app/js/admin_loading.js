(function() {
    var overlay = null;
    var loading = false;
    var escalationTimers = [];

    function ensureOverlay() {
        if (overlay) return overlay;
        overlay = document.createElement("div");
        overlay.id = "pm-admin-loading";
        overlay.className = "pm-admin-loading";
        overlay.setAttribute("role", "status");
        overlay.setAttribute("aria-live", "polite");
        overlay.innerHTML =
            "<div class='pm-admin-loading-card'>" +
                "<div class='pm-admin-loading-spinner' aria-hidden='true'></div>" +
                "<p class='pm-admin-loading-title'>読み込み中</p>" +
            "</div>";
        document.body.appendChild(overlay);
        return overlay;
    }

    function setText(title) {
        var node = ensureOverlay();
        var titleNode = node.querySelector(".pm-admin-loading-title");
        if (titleNode && title) titleNode.textContent = title;
    }

    function clearTimers() {
        escalationTimers.forEach(function(timerId) { clearTimeout(timerId); });
        escalationTimers = [];
    }

    function show(title) {
        loading = true;
        setText(title || "読み込み中");
        ensureOverlay().classList.add("is-visible");
        document.documentElement.classList.add("pm-admin-loading-active");
        clearTimers();
    }

    function hide() {
        loading = false;
        clearTimers();
        document.documentElement.classList.remove("pm-admin-loading-active");
        if (overlay) overlay.classList.remove("is-visible");
        document.querySelectorAll("form[data-admin-loading-submitting='1']").forEach(function(form) {
            form.dataset.adminLoadingSubmitting = "";
            form.classList.remove("is-admin-submitting");
            form.querySelectorAll("button[type='submit'], input[type='submit']").forEach(function(control) {
                control.disabled = false;
            });
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
        if (link.closest(".calendarbox, .clockbox, .selector, .select2-container")) return true;

        try {
            var url = new URL(link.href, window.location.href);
            if (url.origin !== window.location.origin) return true;
            if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) return true;
        } catch (error) {
            return true;
        }
        return false;
    }

    function preserveSubmitter(form, submitter) {
        form.querySelectorAll("input[data-admin-loading-preserved='1']").forEach(function(node) { node.remove(); });
        if (!submitter || !submitter.name) return;
        var hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = submitter.name;
        hidden.value = submitter.value || "1";
        hidden.setAttribute("data-admin-loading-preserved", "1");
        form.appendChild(hidden);
    }

    function shouldSkipForm(form) {
        if (!form || form.dataset.noPageLoading === "1") return true;
        if (form.dataset.dupForm !== undefined) return true;
        if (form.querySelector('input[type="file"][name="video_file"][data-direct-upload-url]')) return true;
        return false;
    }

    function bind() {
        document.addEventListener("click", function(event) {
            var link = event.target.closest && event.target.closest("a[href]");
            if (isSkippableLink(link, event)) return;
            if (loading) {
                event.preventDefault();
                return;
            }
            link.classList.add("is-admin-loading-source");
            show("読み込み中");
        }, true);

        document.addEventListener("submit", function(event) {
            var form = event.target;
            if (shouldSkipForm(form)) return;
            if (form.dataset.adminLoadingSubmitting === "1") {
                event.preventDefault();
                return;
            }
            preserveSubmitter(form, event.submitter);
            form.dataset.adminLoadingSubmitting = "1";
            form.classList.add("is-admin-submitting");
            show("読み込み中");
            setTimeout(function() {
                form.querySelectorAll("button[type='submit'], input[type='submit']").forEach(function(control) {
                    control.disabled = true;
                });
            }, 0);
        }, true);

        window.addEventListener("pageshow", hide);
        window.addEventListener("pagehide", clearTimers);
    }

    window.MapAdminLoading = {
        show: show,
        hide: hide,
        isLoading: function() { return loading; }
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bind, { once: true });
    } else {
        bind();
    }
})();
