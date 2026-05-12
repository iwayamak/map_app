var IMAGE_MODAL_ANIMATION_MS = 220;
var imageModalCloseTimer = null;
var GALLERY_MORPH_MS = 380;

function fitSizeInBox(naturalWidth, naturalHeight, boxWidth, boxHeight) {
    if (!naturalWidth || !naturalHeight || !boxWidth || !boxHeight) {
        return { width: boxWidth || 1, height: boxHeight || 1 };
    }
    var ratio = Math.min(boxWidth / naturalWidth, boxHeight / naturalHeight);
    return {
        width: Math.max(1, naturalWidth * ratio),
        height: Math.max(1, naturalHeight * ratio),
    };
}

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
        if (wrapper) wrapper.classList.add("is-switching");

        var box = wrapper ? wrapper.getBoundingClientRect() : { width: 1, height: 1 };
        var oldNaturalWidth = mainImage.naturalWidth || preload.naturalWidth || 1;
        var oldNaturalHeight = mainImage.naturalHeight || preload.naturalHeight || 1;
        var oldFit = fitSizeInBox(oldNaturalWidth, oldNaturalHeight, Math.max(box.width, 1), Math.max(box.height, 1));
        var newFit = fitSizeInBox(preload.naturalWidth, preload.naturalHeight, Math.max(box.width, 1), Math.max(box.height, 1));
        var scaleX = Math.max(0.72, Math.min(1.38, oldFit.width / Math.max(newFit.width, 1)));
        var scaleY = Math.max(0.72, Math.min(1.38, oldFit.height / Math.max(newFit.height, 1)));

        mainImage.src = imageUrl;
        if (fullImageUrl) {
            mainImage.dataset.fullUrl = fullImageUrl;
        }
        if (stageBg) {
            stageBg.style.backgroundImage = "url(\"" + imageUrl.replace(/"/g, '\\"') + "\")";
        }
        applyImageLoadingState(mainImage, wrapper);

        var settle = function() {
            mainImage.style.transition = "none";
            mainImage.style.transform = "scale(" + scaleX.toFixed(4) + "," + scaleY.toFixed(4) + ")";
            void mainImage.offsetWidth;
            mainImage.style.transition = "transform " + GALLERY_MORPH_MS + "ms cubic-bezier(0.22, 1, 0.36, 1)";
            requestAnimationFrame(function() {
                mainImage.style.transform = "scale(1,1)";
            });
            setTimeout(function() {
                mainImage.style.transition = "";
                if (wrapper) wrapper.classList.remove("is-switching");
            }, GALLERY_MORPH_MS + 20);
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
