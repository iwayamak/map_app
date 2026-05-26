var DETAIL_MODAL_ANIMATION_MS = 260;
var detailModalCloseTimer = null;

function showDetailModal(content) {
    var modal = document.getElementById("detailModal");
    var modalContent = document.getElementById("detailModalContent");
    if (!modal || !modalContent) return;

    if (detailModalCloseTimer) {
        clearTimeout(detailModalCloseTimer);
        detailModalCloseTimer = null;
    }

    modalContent.innerHTML = content;
    modal.style.display = "block";
    requestAnimationFrame(function() {
        modal.classList.add("is-open");
    });
    fitModalTitleToSingleLine(modalContent);
    initModalImageLoading(modalContent);
    document.body.style.overflow = "hidden";
}

function fitModalTitleToSingleLine(container) {
    var title = container.querySelector(".activity-modal-title, .performance-modal-title");
    if (!title) return;

    var isMobile = window.matchMedia("(max-width: 768px)").matches;
    var maxFontSize = isMobile ? 24 : 26;
    var minFontSize = isMobile ? 15 : 18;

    function fitNow() {
        if (title.clientWidth <= 0) return false;

        title.style.fontSize = maxFontSize + "px";
        if (title.scrollWidth <= title.clientWidth) return true;

        var nextFontSize = maxFontSize;
        while (title.scrollWidth > title.clientWidth && nextFontSize > minFontSize) {
            nextFontSize -= 1;
            title.style.fontSize = nextFontSize + "px";
        }
        return true;
    }

    if (fitNow()) return;
    requestAnimationFrame(function() {
        fitNow();
    });
    setTimeout(function() {
        fitNow();
    }, 0);
}

function scheduleFitModalTitle() {
    var modal = document.getElementById("detailModal");
    if (!modal || modal.style.display === "none") return;

    var modalContent = document.getElementById("detailModalContent");
    if (!modalContent) return;

    fitModalTitleToSingleLine(modalContent);
    requestAnimationFrame(function() {
        fitModalTitleToSingleLine(modalContent);
    });
}

function applyImageLoadingState(img, host) {
    img.classList.add("is-loading");
    img.classList.remove("is-loaded");
    if (host) host.classList.add("is-loading");

    var finish = function() {
        img.classList.remove("is-loading");
        img.classList.add("is-loaded");
        if (host) host.classList.remove("is-loading");
    };

    if (img.complete && img.naturalWidth > 0) {
        finish();
        return;
    }

    img.addEventListener("load", finish, { once: true });
    img.addEventListener("error", finish, { once: true });
}

function initModalImageLoading(container) {
    var images = container.querySelectorAll(".location-photo-main, .location-photo-thumb img");
    images.forEach(function(img) {
        var host = img.closest(".location-photo-main-wrapper") || img.closest(".location-photo-thumb");
        applyImageLoadingState(img, host);
    });
}

function closeDetailModal() {
    var modal = document.getElementById("detailModal");
    var modalContent = document.getElementById("detailModalContent");
    if (!modal || modal.style.display === "none") return;

    modal.classList.remove("is-open");
    detailModalCloseTimer = setTimeout(function() {
        modal.style.display = "none";
        if (modalContent) modalContent.innerHTML = "";
        detailModalCloseTimer = null;
    }, DETAIL_MODAL_ANIMATION_MS);
    document.body.style.overflow = "";
}

window.addEventListener("resize", scheduleFitModalTitle);
window.addEventListener("orientationchange", scheduleFitModalTitle);
