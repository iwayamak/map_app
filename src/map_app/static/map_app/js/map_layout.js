function syncViewportHeightVariable() {
    var viewportHeight = window.innerHeight;
    if (window.visualViewport && window.visualViewport.height) {
        viewportHeight = window.visualViewport.height;
    }
    if (!viewportHeight) return;
    var vhUnit = viewportHeight * 0.01;
    document.documentElement.style.setProperty("--app-vh", vhUnit + "px");
}

function setupKeyboardViewportFlashGuard() {
    var mapElement = document.querySelector(".folium-map");
    if (!mapElement) return;

    function lockMapHeight() {
        var mapHeight = Math.ceil(mapElement.getBoundingClientRect().height);
        if (!mapHeight) return;
        document.documentElement.style.setProperty("--keyboard-lock-map-height", mapHeight + "px");
        document.body.classList.add("keyboard-focus-active");
    }

    function unlockMapHeight() {
        document.body.classList.remove("keyboard-focus-active");
        document.documentElement.style.removeProperty("--keyboard-lock-map-height");
    }

    document.addEventListener("focusin", function(event) {
        if (!event.target || !event.target.closest(".map-search-input")) return;
        lockMapHeight();
    });

    document.addEventListener("focusout", function(event) {
        if (!event.target || !event.target.closest(".map-search-input")) return;
        setTimeout(unlockMapHeight, 160);
    });
}

function syncMapLayoutWithHeaderHeight() {
    var header = document.getElementById("map-header");
    if (!header) return;
    var searchContainer = document.getElementById("map-search-container");
    var restoreSearchOpen = false;
    var originalTransition = null;

    if (searchContainer && searchContainer.classList.contains("is-open")) {
        restoreSearchOpen = true;
        originalTransition = searchContainer.style.transition;
        searchContainer.style.transition = "none";
        searchContainer.classList.remove("is-open");
        void searchContainer.offsetHeight;
    }

    var measuredHeight = Math.ceil(header.getBoundingClientRect().height);
    if (restoreSearchOpen) {
        searchContainer.classList.add("is-open");
        void searchContainer.offsetHeight;
        searchContainer.style.transition = originalTransition || "";
    }
    if (!measuredHeight) return;

    document.documentElement.style.setProperty("--map-header-height", measuredHeight + "px");

    var spacer = document.getElementById("map-header-spacer");
    if (spacer) {
        spacer.style.height = measuredHeight + "px";
    }
}

function fitHeaderTextToSingleLine() {
    var header = document.getElementById("map-header");
    if (!header) return;

    var title = header.querySelector(".map-header-title");
    var subtitle = header.querySelector(".map-header-subtitle");
    if (!title || !subtitle) return;
    var textWrap = header.querySelector(".map-header-text");
    if (!textWrap) return;

    if (window.innerWidth > 768) {
        title.style.fontSize = "";
        subtitle.style.fontSize = "";
        return;
    }

    var availableWidth = Math.floor(textWrap.getBoundingClientRect().width);
    if (!availableWidth) return;

    var maxTitle = 16;
    var minTitle = 13;
    var maxSubtitle = 12;
    var minSubtitle = 10;
    var ratio = maxSubtitle / maxTitle;
    var titleSize = maxTitle;

    function applySizes(nextTitleSize) {
        var boundedTitle = Math.max(minTitle, Math.min(maxTitle, nextTitleSize));
        var nextSubtitleSize = Math.max(minSubtitle, Math.min(maxSubtitle, boundedTitle * ratio));
        title.style.fontSize = boundedTitle + "px";
        subtitle.style.fontSize = nextSubtitleSize + "px";
    }

    applySizes(titleSize);
    while ((title.scrollWidth > availableWidth || subtitle.scrollWidth > availableWidth) && titleSize > minTitle) {
        titleSize -= 0.5;
        applySizes(titleSize);
    }
}

function preventMobileDoubleTapZoomOnHeader() {
    if (window.innerWidth > 768) return;

    var guardedSelectors = ["#map-header", "#map-search-container", "#hamburger-menu", "#statistics-panel"];
    var lastTapAt = 0;

    function isFormControl(target) {
        if (!target) return false;
        return Boolean(
            target.closest(
                "input, textarea, select, option, label, summary, details, button, a, [role='button'], [contenteditable='true']"
            )
        );
    }

    guardedSelectors.forEach(function(selector) {
        var element = document.querySelector(selector);
        if (!element) return;

        element.addEventListener("dblclick", function(event) {
            if (isFormControl(event.target)) return;
            event.preventDefault();
        });

        element.addEventListener("touchend", function(event) {
            if (isFormControl(event.target)) return;
            var now = Date.now();
            if (now - lastTapAt < 320) {
                event.preventDefault();
            }
            lastTapAt = now;
        }, { passive: false });
    });
}

document.addEventListener("DOMContentLoaded", function() {
    syncViewportHeightVariable();
    setupKeyboardViewportFlashGuard();
    syncMapLayoutWithHeaderHeight();
    fitHeaderTextToSingleLine();
    preventMobileDoubleTapZoomOnHeader();
    setTimeout(syncViewportHeightVariable, 0);
    setTimeout(syncMapLayoutWithHeaderHeight, 0);
    setTimeout(fitHeaderTextToSingleLine, 0);
});

window.addEventListener("load", function() {
    syncViewportHeightVariable();
    syncMapLayoutWithHeaderHeight();
    fitHeaderTextToSingleLine();
});

window.addEventListener("resize", function() {
    syncViewportHeightVariable();
    syncMapLayoutWithHeaderHeight();
    fitHeaderTextToSingleLine();
});

if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", syncViewportHeightVariable);
    window.visualViewport.addEventListener("scroll", syncViewportHeightVariable);
}
