var IMAGE_MODAL_ANIMATION_MS = 220;
var GALLERY_SWITCH_ANIMATION_MS = 280;
var imageModalCloseTimer = null;

function showImageModal(imageUrl) {
    var modal = document.getElementById("imageModal");
    var modalImg = document.getElementById("modalImage");
    if (!modal || !modalImg) return;

    if (imageModalCloseTimer) {
        clearTimeout(imageModalCloseTimer);
        imageModalCloseTimer = null;
    }

    modal.style.display = "block";
    modal.classList.add("is-loading");
    modalImg.classList.remove("is-loaded");
    modalImg.classList.add("is-loading");
    modalImg.src = imageUrl;

    var finish = function() {
        modal.classList.remove("is-loading");
        modalImg.classList.remove("is-loading");
        modalImg.classList.add("is-loaded");
    };

    if (modalImg.complete && modalImg.naturalWidth > 0) {
        finish();
    } else {
        modalImg.addEventListener("load", finish, { once: true });
        modalImg.addEventListener("error", finish, { once: true });
    }

    requestAnimationFrame(function() {
        modal.classList.add("is-open");
    });
    document.body.style.overflow = "hidden";
}

function closeImageModal() {
    var modal = document.getElementById("imageModal");
    if (!modal || modal.style.display === "none") return;

    modal.classList.remove("is-open");
    modal.classList.remove("is-loading");
    imageModalCloseTimer = setTimeout(function() {
        modal.style.display = "none";
        imageModalCloseTimer = null;
    }, IMAGE_MODAL_ANIMATION_MS);
    document.body.style.overflow = "";
}

function setLocationGalleryImage(galleryId, imageUrl, fullImageUrl, thumbButton) {
    var mainImage = document.getElementById(galleryId + "-main");
    if (!mainImage) return;

    var wrapper = mainImage.closest(".location-photo-main-wrapper");
    var stageBg = document.getElementById(galleryId + "-bg");

    var preload = new Image();
    preload.src = imageUrl;

    var applySwitch = function() {
        if (wrapper) {
            var currentHeight = Math.max(mainImage.getBoundingClientRect().height, 120);
            var wrapperWidth = Math.max(wrapper.clientWidth, 1);
            var nextHeight = currentHeight;
            if (preload.naturalWidth > 0 && preload.naturalHeight > 0) {
                var maxHeight = Math.floor(window.innerHeight * 0.7);
                nextHeight = Math.min(
                    maxHeight,
                    Math.round((wrapperWidth * preload.naturalHeight) / preload.naturalWidth)
                );
            }
            wrapper.style.height = currentHeight + "px";
            wrapper.classList.toggle("is-shrinking", nextHeight < currentHeight);
            wrapper.classList.add("is-switching");
            wrapper.offsetHeight;
            wrapper.style.height = nextHeight + "px";
        }

        mainImage.src = imageUrl;
        if (fullImageUrl) {
            mainImage.dataset.fullUrl = fullImageUrl;
        }
        if (stageBg) {
            stageBg.style.backgroundImage = "url(\"" + imageUrl.replace(/"/g, '\\"') + "\")";
        }
        applyImageLoadingState(mainImage, wrapper);

        var settle = function() {
            if (!wrapper) return;
            wrapper.classList.remove("is-switching");
            wrapper.classList.remove("is-shrinking");
            setTimeout(function() {
                wrapper.style.height = "";
            }, GALLERY_SWITCH_ANIMATION_MS);
        };
        mainImage.addEventListener("load", settle, { once: true });
        mainImage.addEventListener("error", settle, { once: true });
    };

    if (preload.complete && preload.naturalWidth > 0) {
        applySwitch();
    } else {
        preload.addEventListener("load", applySwitch, { once: true });
        preload.addEventListener("error", applySwitch, { once: true });
    }

    if (!thumbButton) return;
    var gallery = thumbButton.closest(".location-photo-gallery");
    if (!gallery) return;

    gallery.querySelectorAll(".location-photo-thumb").forEach(function(button) {
        button.classList.remove("is-active");
    });
    thumbButton.classList.add("is-active");
}
