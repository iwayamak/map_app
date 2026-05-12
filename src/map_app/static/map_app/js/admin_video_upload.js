document.addEventListener("DOMContentLoaded", function() {
    var form = document.querySelector("#content-main form");
    if (!form) return;

    var videoInput = form.querySelector('input[type="file"][name="video_file"]');
    if (!videoInput) return;

    var overlay = document.createElement("div");
    overlay.className = "video-upload-overlay";
    overlay.setAttribute("aria-hidden", "true");
    overlay.innerHTML = [
        '<div class="video-upload-overlay-card" role="status" aria-live="polite">',
        '<div class="video-upload-spinner"></div>',
        '<p class="video-upload-title">アップロード処理を開始しています</p>',
        '<p class="video-upload-copy">動画を転送した後に圧縮とサムネイル生成をバックグラウンドで続行します。</p>',
        "</div>",
    ].join("");
    document.body.appendChild(overlay);

    function ensureHiddenField(name) {
        var field = form.querySelector('input[type="hidden"][name="' + name + '"]');
        if (field) return field;
        field = document.createElement("input");
        field.type = "hidden";
        field.name = name;
        form.appendChild(field);
        return field;
    }

    var hiddenDirectKey = ensureHiddenField("direct_upload_key");
    var hiddenOriginalName = ensureHiddenField("direct_upload_original_name");
    var hiddenSize = ensureHiddenField("direct_upload_size");
    var hiddenContentType = ensureHiddenField("direct_upload_content_type");
    var hiddenSubmitterName = null;

    function clearDirectUploadFields() {
        hiddenDirectKey.value = "";
        hiddenOriginalName.value = "";
        hiddenSize.value = "";
        hiddenContentType.value = "";
        form.dataset.directUploadComplete = "";
    }

    function preserveSubmitter(submitter) {
        if (hiddenSubmitterName) {
            var staleField = form.querySelector('input[type="hidden"][name="' + hiddenSubmitterName + '"][data-submit-preserved="1"]');
            if (staleField) staleField.remove();
            hiddenSubmitterName = null;
        }
        if (!submitter || !submitter.name) return;
        var hiddenField = document.createElement("input");
        hiddenField.type = "hidden";
        hiddenField.name = submitter.name;
        hiddenField.value = submitter.value || "1";
        hiddenField.setAttribute("data-submit-preserved", "1");
        form.appendChild(hiddenField);
        hiddenSubmitterName = submitter.name;
    }

    function disableSubmitButtons(disabled) {
        form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(function(element) {
            element.disabled = disabled;
        });
    }

    function showOverlay(title, copy) {
        var titleNode = overlay.querySelector(".video-upload-title");
        var copyNode = overlay.querySelector(".video-upload-copy");
        if (titleNode) titleNode.textContent = title;
        if (copyNode) copyNode.textContent = copy;
        overlay.classList.add("is-visible");
    }

    function hideOverlay() {
        overlay.classList.remove("is-visible");
    }

    function getCookie(name) {
        var cookieValue = null;
        if (!document.cookie) return cookieValue;
        document.cookie.split(";").forEach(function(cookie) {
            var trimmed = cookie.trim();
            if (trimmed.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(trimmed.substring(name.length + 1));
            }
        });
        return cookieValue;
    }

    async function requestDirectUpload(file) {
        var response = await fetch(videoInput.dataset.directUploadUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({
                filename: file.name,
                content_type: file.type || "application/octet-stream",
                size: file.size
            }),
            credentials: "same-origin"
        });

        var payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.error || "S3アップロードURLの取得に失敗しました。");
        }
        return payload;
    }

    async function uploadFileToS3(uploadUrl, file, contentType) {
        var response = await fetch(uploadUrl, {
            method: "PUT",
            headers: {
                "Content-Type": contentType
            },
            body: file,
            mode: "cors"
        });
        if (!response.ok) {
            throw new Error("S3への動画アップロードに失敗しました。");
        }
    }

    videoInput.addEventListener("change", function() {
        clearDirectUploadFields();
    });

    form.addEventListener("submit", function(event) {
        preserveSubmitter(event.submitter);
        if (form.dataset.submitting === "1") {
            event.preventDefault();
            return;
        }

        var directUploadEnabled = videoInput.dataset.directUploadEnabled === "1";
        var selectedFile = videoInput.files && videoInput.files[0];
        if (!directUploadEnabled || !selectedFile || form.dataset.directUploadComplete === "1") {
            form.dataset.submitting = "1";
            showOverlay("アップロード処理を開始しています", "保存後に圧縮とサムネイル生成をバックグラウンドで続行します。");
            disableSubmitButtons(true);
            return;
        }

        event.preventDefault();
        if (form.dataset.uploading === "1") {
            return;
        }

        form.dataset.uploading = "1";
        disableSubmitButtons(true);
        showOverlay("S3へ動画をアップロードしています", "この転送が終わると通常の保存処理へ進みます。");

        requestDirectUpload(selectedFile)
            .then(function(payload) {
                return uploadFileToS3(payload.upload_url, selectedFile, payload.content_type).then(function() {
                    hiddenDirectKey.value = payload.relative_key;
                    hiddenOriginalName.value = selectedFile.name;
                    hiddenSize.value = String(selectedFile.size);
                    hiddenContentType.value = selectedFile.type || payload.content_type;
                    videoInput.value = "";
                    form.dataset.directUploadComplete = "1";
                    form.dataset.submitting = "1";
                    showOverlay("保存処理を実行しています", "アップロード済み動画を登録し、圧縮とサムネイル生成をバックグラウンドで続行します。");
                    form.submit();
                });
            })
            .catch(function(error) {
                form.dataset.uploading = "0";
                form.dataset.submitting = "";
                form.dataset.directUploadComplete = "";
                hideOverlay();
                disableSubmitButtons(false);
                window.alert(error.message || "動画アップロードに失敗しました。");
            });
    });
});
