(function () {
    function getEndpoint() {
        var listNode = document.querySelector("[data-video-status-endpoint]");
        if (listNode) {
            return listNode.getAttribute("data-video-status-endpoint");
        }
        var formNode = document.querySelector('meta[name="video-status-endpoint"]');
        return formNode ? formNode.getAttribute("content") : "";
    }

    function getTrackedIds() {
        var ids = new Set();
        document.querySelectorAll("[data-video-status-label]").forEach(function (node) {
            ids.add(node.getAttribute("data-video-status-label"));
        });
        document.querySelectorAll("[data-video-progress-text]").forEach(function (node) {
            ids.add(node.getAttribute("data-video-progress-text"));
        });
        document.querySelectorAll("[data-video-progress-percent]").forEach(function (node) {
            ids.add(node.getAttribute("data-video-progress-percent"));
        });
        document.querySelectorAll("[data-video-step-text]").forEach(function (node) {
            ids.add(node.getAttribute("data-video-step-text"));
        });
        document.querySelectorAll("[data-video-error-text]").forEach(function (node) {
            ids.add(node.getAttribute("data-video-error-text"));
        });
        var formIdNode = document.querySelector('meta[name="video-status-id"]');
        if (formIdNode) {
            ids.add(formIdNode.getAttribute("content"));
        }
        return Array.from(ids).filter(Boolean);
    }

    function updateStatusLabel(video) {
        document.querySelectorAll('[data-video-status-label="' + video.id + '"]').forEach(function (node) {
            node.textContent = video.processing_status_display;
            node.setAttribute("data-video-status", video.processing_status);
            if (node.classList.contains("video-admin-chip-status")) {
                node.className = "video-admin-chip video-admin-chip-status video-admin-chip-status-" + video.processing_status;
            }
        });
    }

    function updateProgressText(video) {
        var text = video.processing_progress_percent + "% / " + video.processing_step_display;
        document.querySelectorAll('[data-video-progress-bar="' + video.id + '"]').forEach(function (node) {
            node.style.width = video.processing_progress_percent + "%";
        });
        document.querySelectorAll('[data-video-progress-text="' + video.id + '"]').forEach(function (node) {
            node.textContent = text;
        });
        document.querySelectorAll('[data-video-progress-percent="' + video.id + '"]').forEach(function (node) {
            node.textContent = video.processing_progress_percent + "%";
        });
        document.querySelectorAll('[data-video-step-text="' + video.id + '"]').forEach(function (node) {
            node.textContent = video.processing_step_display;
        });
    }

    function updateErrorText(video) {
        document.querySelectorAll('[data-video-error-text="' + video.id + '"]').forEach(function (node) {
            var text = video.processing_error || "";
            if (!text) {
                if (node.classList.contains("video-admin-card-error")) {
                    node.hidden = true;
                    node.textContent = "";
                } else {
                    node.textContent = "-";
                }
                return;
            }
            node.hidden = false;
            node.textContent = text;
        });
    }

    function shouldContinue(videos) {
        return videos.some(function (video) {
            return video.processing_status === "pending" || video.processing_status === "running";
        });
    }

    function boot() {
        var endpoint = getEndpoint();
        var ids = getTrackedIds();
        if (!endpoint || ids.length === 0) {
            return;
        }

        var active = true;
        var timerId = null;

        function poll() {
            if (!active || document.hidden) {
                timerId = window.setTimeout(poll, 5000);
                return;
            }

            fetch(endpoint + "?ids=" + encodeURIComponent(ids.join(",")), {
                credentials: "same-origin",
                headers: {"X-Requested-With": "XMLHttpRequest"}
            })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error("status fetch failed");
                    }
                    return response.json();
                })
                .then(function (payload) {
                    var videos = payload.videos || [];
                    videos.forEach(function (video) {
                        updateStatusLabel(video);
                        updateProgressText(video);
                        updateErrorText(video);
                    });
                    active = shouldContinue(videos);
                })
                .catch(function () {
                    active = true;
                })
                .finally(function () {
                    if (active) {
                        timerId = window.setTimeout(poll, 5000);
                    }
                });
        }

        poll();

        window.addEventListener("beforeunload", function () {
            if (timerId) {
                window.clearTimeout(timerId);
            }
            active = false;
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
