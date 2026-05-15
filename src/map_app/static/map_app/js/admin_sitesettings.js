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

    function buildEmojiButton(emoji, inputEl) {
        var button = document.createElement("button");
        button.type = "button";
        button.className = "emoji-picker-button";
        button.textContent = emoji;
        button.setAttribute("aria-label", "絵文字 " + emoji + " を選択");
        button.addEventListener("click", function () {
            inputEl.value = emoji;
            inputEl.dispatchEvent(new Event("input", { bubbles: true }));
            inputEl.dispatchEvent(new Event("change", { bubbles: true }));
        });
        return button;
    }

    function attachEmojiPicker(inputId) {
        var inputEl = document.getElementById(inputId);
        if (!inputEl || inputEl.dataset.emojiPickerAttached === "1") return;

        var row = findFieldRow(inputId);
        if (!row) return;

        var picker = document.createElement("div");
        picker.className = "emoji-picker-grid";
        EMOJI_CHOICES.forEach(function (emoji) {
            picker.appendChild(buildEmojiButton(emoji, inputEl));
        });

        var clearButton = document.createElement("button");
        clearButton.type = "button";
        clearButton.className = "emoji-picker-clear";
        clearButton.textContent = "クリア";
        clearButton.addEventListener("click", function () {
            inputEl.value = "";
            inputEl.dispatchEvent(new Event("input", { bubbles: true }));
            inputEl.dispatchEvent(new Event("change", { bubbles: true }));
        });

        var wrapper = document.createElement("div");
        wrapper.className = "emoji-picker-wrap";
        wrapper.appendChild(picker);
        wrapper.appendChild(clearButton);

        row.appendChild(wrapper);
        inputEl.dataset.emojiPickerAttached = "1";
    }

    function injectEmojiPickerStyle() {
        if (document.getElementById("admin-sitesettings-emoji-style")) return;
        var style = document.createElement("style");
        style.id = "admin-sitesettings-emoji-style";
        style.textContent = ""
            + ".emoji-picker-wrap{margin-top:8px;display:grid;gap:8px;}"
            + ".emoji-picker-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(34px,1fr));gap:6px;max-width:420px;}"
            + ".emoji-picker-button{height:34px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer;font-size:18px;line-height:1;}"
            + ".emoji-picker-button:hover{background:#f9fafb;border-color:#94a3b8;}"
            + ".emoji-picker-clear{justify-self:start;height:30px;padding:0 10px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer;font-size:12px;}";
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
