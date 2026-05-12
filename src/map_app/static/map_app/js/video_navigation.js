document.addEventListener("DOMContentLoaded", function() {
    var hamburgerButton = document.getElementById("hamburger-button");
    var hamburgerClose = document.getElementById("hamburger-close");
    var hamburgerMenu = document.getElementById("hamburger-menu");
    var menuOverlay = document.getElementById("menu-overlay");
    var openMapButton = document.getElementById("open-map-button");
    var openVideosButton = document.getElementById("open-videos-button");
    var openAdminButton = document.getElementById("open-admin-button");

    function updateHamburgerIcon(isOpen) {
        if (!hamburgerButton) return;
        var lines = hamburgerButton.querySelectorAll(".hamburger-line");
        if (lines.length !== 3) return;
        lines[0].style.transform = isOpen ? "translateY(8px) rotate(45deg)" : "";
        lines[1].style.opacity = isOpen ? "0" : "";
        lines[2].style.transform = isOpen ? "translateY(-8px) rotate(-45deg)" : "";
    }

    function toggleHamburgerMenu(forceOpen) {
        if (!hamburgerMenu || !menuOverlay) return;
        var nextOpen = typeof forceOpen === "boolean" ? forceOpen : hamburgerMenu.style.right !== "0px";
        hamburgerMenu.style.right = nextOpen ? "0px" : "-100%";
        menuOverlay.style.opacity = nextOpen ? "1" : "0";
        menuOverlay.style.visibility = nextOpen ? "visible" : "hidden";
        document.body.style.overflow = nextOpen ? "hidden" : "";
        updateHamburgerIcon(nextOpen);
    }

    function bindRedirect(button, url) {
        if (!button) return;
        button.addEventListener("click", function() {
            window.location.href = url;
        });
    }

    if (hamburgerButton) {
        hamburgerButton.addEventListener("click", function() {
            toggleHamburgerMenu();
        });
    }
    if (hamburgerClose) {
        hamburgerClose.addEventListener("click", function() {
            toggleHamburgerMenu(false);
        });
    }
    if (menuOverlay) {
        menuOverlay.addEventListener("click", function() {
            toggleHamburgerMenu(false);
        });
    }

    bindRedirect(openMapButton, "/");
    bindRedirect(openVideosButton, "/videos/");
    bindRedirect(openAdminButton, "/admin/");

    document.addEventListener("keydown", function(event) {
        if (event.key !== "Escape") return;
        if (hamburgerMenu && hamburgerMenu.style.right === "0px") {
            toggleHamburgerMenu(false);
        }
    });
});
