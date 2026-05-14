(function () {
    function findFieldRow(inputId) {
        var el = document.getElementById(inputId);
        if (!el) return null;
        return el.closest(".form-row, .fieldBox, .field-" + inputId.replace(/^id_/, ""));
    }

    function setVisible(row, visible) {
        if (!row) return;
        row.style.display = visible ? "" : "none";
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
    });
})();
