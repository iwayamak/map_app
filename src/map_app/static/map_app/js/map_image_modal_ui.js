var IMAGE_MODAL_ANIMATION_MS = 220;
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
    mainImage.src = imageUrl;
    if (fullImageUrl) {
        mainImage.dataset.fullUrl = fullImageUrl;
    }
    applyImageLoadingState(mainImage, wrapper);

    if (!thumbButton) return;
    var gallery = thumbButton.closest(".location-photo-gallery");
    if (!gallery) return;

    gallery.querySelectorAll(".location-photo-thumb").forEach(function(button) {
        button.classList.remove("is-active");
    });
    thumbButton.classList.add("is-active");
}
