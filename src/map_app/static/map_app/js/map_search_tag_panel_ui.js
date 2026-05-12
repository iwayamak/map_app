(function(global) {
    function createTagPanelUi(elements, searchState, utils) {
        function syncTagSummaryCount() {
            if (!elements.tagFilter) return;

            var summary = elements.tagFilter.querySelector("summary");
            if (!summary) return;

            var countNode = summary.querySelector(".map-tag-count");
            var count = searchState.getSelectedCheckboxes().length;
            if (count <= 0) {
                if (countNode) countNode.remove();
                return;
            }

            if (!countNode) {
                countNode = document.createElement("span");
                countNode.className = "map-tag-count";
                summary.appendChild(countNode);
            }
            countNode.textContent = String(count);
        }

        function renderSelectedTags() {
            if (!elements.selectedTagList) return;

            var selected = searchState.getSelectedCheckboxes();
            var chips = selected.map(function(checkbox) {
                var color = checkbox.getAttribute("data-tag-color") || "#4b5563";
                var textColor = checkbox.getAttribute("data-tag-text-color") || "#f9fafb";
                return (
                    "<button type='button' class='map-tag-selected-item' data-tag-remove='" + utils.escapeHtml(checkbox.value) + "' style='background: " + utils.escapeHtml(color) + "; color: " + utils.escapeHtml(textColor) + ";'>" +
                        "<span>" + utils.escapeHtml(checkbox.value) + "</span>" +
                        "<span class='map-tag-selected-remove' aria-hidden='true'>×</span>" +
                    "</button>"
                );
            }).join("");
            var clearAllButton = selected.length > 0
                ? "<button type='button' class='map-tag-selected-clear' data-tag-clear-all='1'>すべて解除</button>"
                : "";

            elements.selectedTagList.innerHTML = chips + clearAllButton;
        }

        function sync() {
            renderSelectedTags();
            syncTagSummaryCount();
        }

        return {
            sync: sync,
            renderSelectedTags: renderSelectedTags,
            syncTagSummaryCount: syncTagSummaryCount,
        };
    }

    global.MapSearchTagPanelUi = {
        create: createTagPanelUi,
    };
})(window);
