function updateHamburgerIcon(isOpen) {
    var button = document.getElementById("hamburger-button");
    if (!button) return;

    var lines = button.querySelectorAll(".hamburger-line");
    if (lines.length !== 3) return;

    if (isOpen) {
        lines[0].style.transform = "translateY(8px) rotate(45deg)";
        lines[1].style.opacity = "0";
        lines[2].style.transform = "translateY(-8px) rotate(-45deg)";
    } else {
        lines[0].style.transform = "";
        lines[1].style.opacity = "";
        lines[2].style.transform = "";
    }
}

function toggleHamburgerMenu() {
    var menu = document.getElementById("hamburger-menu");
    var overlay = document.getElementById("menu-overlay");
    var statsPanel = document.getElementById("statistics-panel");
    var isOpen = menu && menu.style.right === "0px";

    if (!menu || !overlay) return;

    if (isOpen) {
        menu.style.right = "-100%";
        overlay.style.opacity = "0";
        overlay.style.visibility = "hidden";
        document.body.style.overflow = "";
        updateHamburgerIcon(false);
        return;
    }

    if (statsPanel && statsPanel.style.opacity === "1") {
        toggleStatistics();
    }

    menu.style.right = "0px";
    overlay.style.opacity = "1";
    overlay.style.visibility = "visible";
    document.body.style.overflow = "hidden";
    updateHamburgerIcon(true);
}

function toggleStatistics() {
    var statsPanel = document.getElementById("statistics-panel");
    var statsOverlay = document.getElementById("statistics-overlay");
    var menu = document.getElementById("hamburger-menu");
    var overlay = document.getElementById("menu-overlay");
    var isVisible = statsPanel && statsPanel.style.opacity === "1";

    if (!statsPanel || !statsOverlay) return;

    if (!isVisible) {
        statsPanel.style.display = "block";
        statsOverlay.style.opacity = "1";
        statsOverlay.style.visibility = "visible";
        setTimeout(function () {
            statsPanel.style.opacity = "1";
            statsPanel.style.transform = "translateX(0)";
        }, 10);
        window.dispatchEvent(new Event("statistics:open"));
        document.body.classList.add("stats-panel-open");

        if (menu) menu.style.right = "-100%";
        if (overlay) {
            overlay.style.opacity = "0";
            overlay.style.visibility = "hidden";
        }
        document.body.style.overflow = "hidden";
        updateHamburgerIcon(false);
        return;
    }

    statsPanel.style.opacity = "0";
    statsPanel.style.transform = "translateX(100%)";
    statsOverlay.style.opacity = "0";
    statsOverlay.style.visibility = "hidden";
    document.body.classList.remove("stats-panel-open");
    document.body.style.overflow = "";
    setTimeout(function () {
        statsPanel.style.display = "none";
    }, 300);
}

function bindPanelEvents() {
    var hamburgerButton = document.getElementById("hamburger-button");
    var hamburgerClose = document.getElementById("hamburger-close");
    var menuOverlay = document.getElementById("menu-overlay");
    var openStatsButton = document.getElementById("open-statistics-button");
    var statsClose = document.getElementById("stats-close-button");
    var statsOverlay = document.getElementById("statistics-overlay");
    var openAdminButton = document.getElementById("open-admin-button");
    var openVideosButton = document.getElementById("open-videos-button");

    function redirectWithLoading(url, title) {
        if (window.MapAppPageLoading && typeof window.MapAppPageLoading.navigate === "function") {
            window.MapAppPageLoading.navigate(url, {
                title: title || "ページを開いています...",
                copy: "タップは受け付け済みです。そのままお待ちください。"
            });
            return;
        }
        window.location.assign(url);
    }

    if (hamburgerButton) hamburgerButton.addEventListener("click", toggleHamburgerMenu);
    if (hamburgerClose) hamburgerClose.addEventListener("click", toggleHamburgerMenu);
    if (menuOverlay) menuOverlay.addEventListener("click", toggleHamburgerMenu);
    if (openStatsButton) openStatsButton.addEventListener("click", toggleStatistics);
    if (statsClose) statsClose.addEventListener("click", toggleStatistics);
    if (statsOverlay) statsOverlay.addEventListener("click", toggleStatistics);
    if (openAdminButton) {
        openAdminButton.addEventListener("click", function () {
            redirectWithLoading("/admin/", "管理画面を開いています...");
        });
    }
    if (openVideosButton) {
        openVideosButton.addEventListener("click", function () {
            redirectWithLoading("/videos/", "動画ライブラリを開いています...");
        });
    }
}

document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;

    var statsPanel = document.getElementById("statistics-panel");
    if (statsPanel && statsPanel.style.opacity === "1") {
        toggleStatistics();
        return;
    }

    var menu = document.getElementById("hamburger-menu");
    if (menu && menu.style.right === "0px") {
        toggleHamburgerMenu();
    }
});

document.addEventListener("DOMContentLoaded", bindPanelEvents);
