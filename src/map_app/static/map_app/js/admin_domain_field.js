(function () {
    function toSnakeCase(value) {
        var text = String(value || "").trim().toLowerCase();
        text = text
            .replace(/['"`]/g, "")
            .replace(/[^a-z0-9]+/g, "_")
            .replace(/^_+|_+$/g, "")
            .replace(/_+/g, "_");
        if (!text) return "";
        if (!/^[a-z]/.test(text)) text = "field_" + text;
        return text;
    }

    function buildSuggestionFromExamples(suggestionsCsv) {
        if (!suggestionsCsv) return "custom_field";
        var suggestions = suggestionsCsv
            .split(",")
            .map(function (item) { return item.trim(); })
            .filter(Boolean);
        return suggestions[0] || "custom_field";
    }

    function mount() {
        var labelInput = document.getElementById("id_label");
        var keyInput = document.getElementById("id_key");
        if (!labelInput || !keyInput) return;
        if (document.getElementById("generate-key-button")) return;

        var button = document.createElement("button");
        button.type = "button";
        button.id = "generate-key-button";
        button.className = "button";
        button.style.marginLeft = "8px";
        button.textContent = "表示名から自動生成";

        button.addEventListener("click", function () {
            var generated = toSnakeCase(labelInput.value);
            if (!generated) {
                generated = buildSuggestionFromExamples(keyInput.dataset.keySuggestions);
            }
            keyInput.value = generated;
            keyInput.dispatchEvent(new Event("input", { bubbles: true }));
            keyInput.focus();
        });

        keyInput.insertAdjacentElement("afterend", button);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", mount);
    } else {
        mount();
    }
})();
