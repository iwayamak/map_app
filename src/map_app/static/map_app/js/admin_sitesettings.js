(function () {
    var EMOJI_CHOICES = [
        "⛩️", "🎹", "📊", "📈", "🕒", "🏆", "📍", "🗺️", "📝", "🏷️",
        "🎵", "📅", "🌸", "🍁", "❄️", "☀️", "🌙", "⭐", "🧭", "🧱",
        "🏛️", "🙏", "🧿", "📿", "🪷", "🧳", "🚶", "🚉", "🚗", "🚌"
    ];

    function findFieldRow(inputId) {
        var el = document.getElementById(inputId);
        if (!el) return null;
        return el.closest(".form-row, .fieldBox, .field-" + inputId.replace(/^id_/, ""));
    }

    function setVisible(row, visible) {
        if (!row) return;
        row.style.display = visible ? "" : "none";
    }

    var activeInputEl = null;
    var pickerOverlayEl = null;
    var pickerDialogEl = null;
    var pickerGridEl = null;

    function buildEmojiButton(emoji, onSelect) {
        var button = document.createElement("button");
        button.type = "button";
        button.className = "emoji-picker-button";
        button.textContent = emoji;
        button.setAttribute("aria-label", "絵文字 " + emoji + " を選択");
        button.addEventListener("click", function () {
            onSelect(emoji);
        });
        return button;
    }

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
    }

    function ensureEmojiModal() {
        if (pickerOverlayEl) return;

        pickerOverlayEl = document.createElement("div");
        pickerOverlayEl.className = "emoji-picker-overlay";
        pickerOverlayEl.style.display = "none";

        pickerDialogEl = document.createElement("div");
        pickerDialogEl.className = "emoji-picker-dialog";
        pickerDialogEl.setAttribute("role", "dialog");
        pickerDialogEl.setAttribute("aria-modal", "true");
        pickerDialogEl.setAttribute("aria-label", "絵文字選択");

        var header = document.createElement("div");
        header.className = "emoji-picker-header";
        header.textContent = "絵文字を選択";

        pickerGridEl = document.createElement("div");
        pickerGridEl.className = "emoji-picker-grid";
        EMOJI_CHOICES.forEach(function (emoji) {
            pickerGridEl.appendChild(buildEmojiButton(emoji, function (selected) {
                setEmojiToActiveInput(selected);
                closeEmojiModal();
            }));
        });

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

        pickerDialogEl.appendChild(header);
        pickerDialogEl.appendChild(pickerGridEl);
        pickerDialogEl.appendChild(footer);
        pickerOverlayEl.appendChild(pickerDialogEl);
        document.body.appendChild(pickerOverlayEl);

        pickerOverlayEl.addEventListener("click", function (event) {
            if (event.target === pickerOverlayEl) {
                closeEmojiModal();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && pickerOverlayEl && pickerOverlayEl.style.display !== "none") {
                closeEmojiModal();
            }
        });
    }

    function attachEmojiPicker(inputId) {
        var inputEl = document.getElementById(inputId);
        if (!inputEl || inputEl.dataset.emojiPickerAttached === "1") return;

        var triggerButton = document.createElement("button");
        triggerButton.type = "button";
        triggerButton.className = "emoji-picker-open";
        triggerButton.textContent = "絵文字を選ぶ";
        triggerButton.addEventListener("click", function () {
            openEmojiModal(inputEl);
        });

        inputEl.insertAdjacentElement("afterend", triggerButton);
        inputEl.dataset.emojiPickerAttached = "1";
    }

    function injectEmojiPickerStyle() {
        if (document.getElementById("admin-sitesettings-emoji-style")) return;
        var style = document.createElement("style");
        style.id = "admin-sitesettings-emoji-style";
        style.textContent = ""
            + ".emoji-picker-open{margin-left:8px;height:34px;padding:0 10px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer;font-size:12px;vertical-align:middle;}"
            + ".emoji-picker-open:hover{background:#f9fafb;border-color:#94a3b8;}"
            + ".emoji-picker-overlay{position:fixed;inset:0;background:rgba(15,23,42,.45);z-index:10050;align-items:center;justify-content:center;padding:20px;}"
            + ".emoji-picker-dialog{width:min(560px,100%);max-height:min(70vh,560px);overflow:auto;background:#fff;border-radius:10px;padding:14px;box-shadow:0 20px 50px rgba(0,0,0,.25);}"
            + ".emoji-picker-header{font-size:14px;font-weight:700;margin-bottom:10px;}"
            + ".emoji-picker-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(36px,1fr));gap:6px;}"
            + ".emoji-picker-button{height:34px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer;font-size:18px;line-height:1;}"
            + ".emoji-picker-button:hover{background:#f9fafb;border-color:#94a3b8;}"
            + ".emoji-picker-footer{display:flex;justify-content:space-between;gap:8px;margin-top:12px;}"
            + ".emoji-picker-clear,.emoji-picker-close{height:32px;padding:0 12px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer;font-size:12px;}"
            + ".emoji-picker-clear:hover,.emoji-picker-close:hover{background:#f9fafb;border-color:#94a3b8;}";
        document.head.appendChild(style);
    }

    function applyHeaderModeVisibility() {
        var modeEl = document.getElementById("id_header_bg_mode");
        if (!modeEl) return;
        var mode = modeEl.value;

        var solidRow = findFieldRow("id_header_bg_solid_color");
        var gradientFromRow = findFieldRow("id_header_bg_gradient_from");
        var gradientToRow = findFieldRow("id_header_bg_gradient_to");
        var gradientAngleRow = findFieldRow("id_header_bg_gradient_angle");

        var isSolid = mode === "solid";
        setVisible(solidRow, isSolid);
        setVisible(gradientFromRow, !isSolid);
        setVisible(gradientToRow, !isSolid);
        setVisible(gradientAngleRow, !isSolid);
    }

    document.addEventListener("DOMContentLoaded", function () {
        var modeEl = document.getElementById("id_header_bg_mode");
        if (!modeEl) return;
        applyHeaderModeVisibility();
        modeEl.addEventListener("change", applyHeaderModeVisibility);

        injectEmojiPickerStyle();
        ensureEmojiModal();
        [
            "id_header_logo_emoji",
            "id_summary_title_icon",
            "id_modal_title_icon",
            "id_statistics_title_icon",
            "id_statistics_monthly_title_icon",
            "id_statistics_recent_title_icon",
            "id_statistics_top_title_icon"
        ].forEach(attachEmojiPicker);
    });
})();
