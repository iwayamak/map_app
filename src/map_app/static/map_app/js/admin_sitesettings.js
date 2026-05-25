(function () {
    var EMOJI_CHOICES = [
        "⛩️", "🎹", "📊", "📈", "🕒", "🏆", "📍", "🗺️", "📝", "🏷️",
        "🎵", "📅", "🌸", "🍁", "❄️", "☀️", "🌙", "⭐", "🧭", "🧱",
        "🏛️", "🙏", "🧿", "📿", "🪷", "🧳", "🚶", "🚉", "🚗", "🚌"
    ];
    var ICON_FIELD_IDS = [
        "id_header_logo_emoji",
        "id_summary_title_icon",
        "id_modal_title_icon",
        "id_statistics_title_icon",
        "id_statistics_monthly_title_icon",
        "id_statistics_recent_title_icon",
        "id_statistics_top_title_icon",
        "id_statistics_recent_item_title_icon"
    ];
    var RICH_PICKER_TAG = "emoji-picker";
    var RICH_PICKER_SRC = "https://cdn.jsdelivr.net/npm/emoji-picker-element@^1/index.js";

    function findFieldRow(inputId) {
        var el = document.getElementById(inputId);
        return el ? el.closest(".form-row, .fieldBox") : null;
    }

    function setVisible(row, visible) {
        if (!row) return;
        row.style.display = visible ? "" : "none";
    }

    var activeInputEl = null;
    var pickerOverlayEl = null;
    var pickerGridEl = null;
    var richPickerMountEl = null;
    var richPickerPromise = null;

    function setEmojiToActiveInput(emoji) {
        if (!activeInputEl) return;
        activeInputEl.value = emoji || "";
        activeInputEl.dispatchEvent(new Event("input", { bubbles: true }));
        activeInputEl.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function closeEmojiModal() {
        if (!pickerOverlayEl) return;
        pickerOverlayEl.style.display = "none";
        activeInputEl = null;
    }

    function openEmojiModal(inputEl) {
        if (!pickerOverlayEl) return;
        activeInputEl = inputEl;
        pickerOverlayEl.style.display = "flex";
        mountRichPickerIfAvailable();
    }

    function buildFallbackGrid() {
        var grid = document.createElement("div");
        grid.className = "emoji-picker-grid";
        EMOJI_CHOICES.forEach(function (emoji) {
            var button = document.createElement("button");
            button.type = "button";
            button.className = "emoji-picker-button";
            button.textContent = emoji;
            button.setAttribute("aria-label", "絵文字 " + emoji + " を選択");
            button.addEventListener("click", function () {
                setEmojiToActiveInput(emoji);
                closeEmojiModal();
            });
            grid.appendChild(button);
        });
        return grid;
    }

    function ensureEmojiModal() {
        if (pickerOverlayEl) return;

        pickerOverlayEl = document.createElement("div");
        pickerOverlayEl.className = "emoji-picker-overlay";
        pickerOverlayEl.style.display = "none";

        var dialog = document.createElement("div");
        dialog.className = "emoji-picker-dialog";
        dialog.setAttribute("role", "dialog");
        dialog.setAttribute("aria-modal", "true");
        dialog.setAttribute("aria-label", "絵文字選択");

        var header = document.createElement("div");
        header.className = "emoji-picker-header";
        header.textContent = "絵文字を選択";

        richPickerMountEl = document.createElement("div");
        richPickerMountEl.className = "emoji-picker-rich";

        pickerGridEl = buildFallbackGrid();

        var footer = document.createElement("div");
        footer.className = "emoji-picker-footer";

        var clearButton = document.createElement("button");
        clearButton.type = "button";
        clearButton.className = "emoji-picker-clear";
        clearButton.textContent = "クリア";
        clearButton.addEventListener("click", function () {
            setEmojiToActiveInput("");
            closeEmojiModal();
        });

        var closeButton = document.createElement("button");
        closeButton.type = "button";
        closeButton.className = "emoji-picker-close";
        closeButton.textContent = "閉じる";
        closeButton.addEventListener("click", closeEmojiModal);

        footer.appendChild(clearButton);
        footer.appendChild(closeButton);
        dialog.appendChild(header);
        dialog.appendChild(richPickerMountEl);
        dialog.appendChild(pickerGridEl);
        dialog.appendChild(footer);
        pickerOverlayEl.appendChild(dialog);
        document.body.appendChild(pickerOverlayEl);

        pickerOverlayEl.addEventListener("click", function (event) {
            if (event.target === pickerOverlayEl) closeEmojiModal();
        });
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && pickerOverlayEl && pickerOverlayEl.style.display !== "none") {
                closeEmojiModal();
            }
        });
    }

    function ensureRichPickerLoaded() {
        if (window.customElements && window.customElements.get(RICH_PICKER_TAG)) {
            return Promise.resolve(true);
        }
        if (richPickerPromise) return richPickerPromise;
        richPickerPromise = new Promise(function (resolve) {
            var script = document.createElement("script");
            script.type = "module";
            script.async = true;
            script.src = RICH_PICKER_SRC;
            script.onload = function () {
                resolve(Boolean(window.customElements && window.customElements.get(RICH_PICKER_TAG)));
            };
            script.onerror = function () { resolve(false); };
            document.head.appendChild(script);
        });
        return richPickerPromise;
    }

    function mountRichPickerIfAvailable() {
        if (!richPickerMountEl || !pickerGridEl) return;
        ensureRichPickerLoaded().then(function (loaded) {
            if (!loaded || !window.customElements.get(RICH_PICKER_TAG)) {
                richPickerMountEl.style.display = "none";
                pickerGridEl.style.display = "grid";
                return;
            }
            if (!richPickerMountEl.querySelector(RICH_PICKER_TAG)) {
                var picker = document.createElement(RICH_PICKER_TAG);
                picker.setAttribute("locale", "ja");
                picker.setAttribute("theme", "light");
                picker.style.width = "100%";
                picker.style.height = "360px";
                picker.addEventListener("emoji-click", function (event) {
                    var unicode = event && event.detail && event.detail.unicode ? event.detail.unicode : "";
                    if (!unicode) return;
                    setEmojiToActiveInput(unicode);
                    closeEmojiModal();
                });
                richPickerMountEl.appendChild(picker);
            }
            richPickerMountEl.style.display = "block";
            pickerGridEl.style.display = "none";
        });
    }

    function attachEmojiPicker(inputId) {
        var inputEl = document.getElementById(inputId);
        if (!inputEl || inputEl.dataset.emojiPickerAttached === "1") return;

        var formRow = inputEl.closest(".form-row");
        if (formRow) formRow.classList.add("emoji-inline-row");
        inputEl.classList.add("emoji-picker-input");

        var inlineWrap = document.createElement("span");
        inlineWrap.className = "emoji-picker-inline-wrap";
        inputEl.parentNode.insertBefore(inlineWrap, inputEl);
        inlineWrap.appendChild(inputEl);

        var button = document.createElement("button");
        button.type = "button";
        button.className = "emoji-picker-open";
        button.textContent = "絵文字を選ぶ";
        button.addEventListener("click", function () {
            openEmojiModal(inputEl);
        });
        inlineWrap.appendChild(button);
        inputEl.dataset.emojiPickerAttached = "1";
    }

    function injectEmojiPickerStyle() {
        if (document.getElementById("admin-sitesettings-emoji-style")) return;
        var style = document.createElement("style");
        style.id = "admin-sitesettings-emoji-style";
        style.textContent = ""
            + ".emoji-picker-input{color:#111827 !important;width:8ch !important;min-width:8ch !important;max-width:8ch !important;}"
            + ".emoji-picker-open{display:inline-flex !important;align-items:center !important;justify-content:center !important;height:34px;padding:0 10px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer;font-size:12px;color:#111827 !important;white-space:nowrap !important;}"
            + ".emoji-picker-open:hover{background:#f9fafb;border-color:#94a3b8;}"
            + ".emoji-picker-inline-wrap{display:inline-flex !important;align-items:center !important;gap:8px !important;white-space:nowrap !important;}"
            + ".emoji-picker-overlay{position:fixed;inset:0;background:rgba(15,23,42,.45);z-index:10050;align-items:center;justify-content:center;padding:20px;}"
            + ".emoji-picker-dialog{width:min(560px,100%);max-height:min(70vh,560px);overflow:auto;background:#fff;border-radius:10px;padding:14px;box-shadow:0 20px 50px rgba(0,0,0,.25);}"
            + ".emoji-picker-header{font-size:14px;font-weight:700;margin-bottom:10px;color:#0f172a;}"
            + ".emoji-picker-rich{display:none;margin-bottom:8px;}"
            + ".emoji-picker-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(36px,1fr));gap:6px;}"
            + ".emoji-picker-button{height:34px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer;font-size:18px;line-height:1;color:#111827 !important;}"
            + ".emoji-picker-button:hover{background:#f9fafb;border-color:#94a3b8;}"
            + ".emoji-picker-footer{display:flex;justify-content:space-between;gap:8px;margin-top:12px;}"
            + ".emoji-picker-clear,.emoji-picker-close{height:32px;padding:0 12px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer;font-size:12px;color:#0f172a !important;}";
        document.head.appendChild(style);
    }

    function applyHeaderModeVisibility() {
        var modeEl = document.getElementById("id_header_bg_mode");
        if (!modeEl) return;
        var isSolid = modeEl.value === "solid";
        setVisible(findFieldRow("id_header_bg_solid_color"), isSolid);
        setVisible(findFieldRow("id_header_bg_gradient_from"), !isSolid);
        setVisible(findFieldRow("id_header_bg_gradient_to"), !isSolid);
        setVisible(findFieldRow("id_header_bg_gradient_angle"), !isSolid);
    }

    document.addEventListener("DOMContentLoaded", function () {
        var modeEl = document.getElementById("id_header_bg_mode");
        if (modeEl) {
            applyHeaderModeVisibility();
            modeEl.addEventListener("change", applyHeaderModeVisibility);
        }

        injectEmojiPickerStyle();
        ensureEmojiModal();
        ICON_FIELD_IDS.forEach(attachEmojiPicker);
    });
})();
