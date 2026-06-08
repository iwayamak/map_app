document.addEventListener("DOMContentLoaded", function() {
    var confirmOverlay = document.getElementById("dup-confirm-overlay");
    var confirmMessage = document.getElementById("dup-confirm-message");
    var confirmOkButton = document.getElementById("dup-confirm-ok");
    var confirmCancelButton = document.getElementById("dup-confirm-cancel");
    var confirmResolver = null;

    function openConfirm(message) {
        return new Promise(function(resolve) {
            confirmResolver = resolve;
            if (confirmMessage) {
                confirmMessage.textContent = message || "実行しますか？";
            }
            if (confirmOverlay) {
                confirmOverlay.classList.add("is-open");
                confirmOverlay.setAttribute("aria-hidden", "false");
            }
        });
    }

    function closeConfirm(result) {
        if (confirmOverlay) {
            confirmOverlay.classList.remove("is-open");
            confirmOverlay.setAttribute("aria-hidden", "true");
        }
        if (typeof confirmResolver === "function") {
            var resolver = confirmResolver;
            confirmResolver = null;
            resolver(Boolean(result));
        }
    }

    if (confirmOkButton) {
        confirmOkButton.addEventListener("click", function() {
            if (confirmOkButton.dataset.processing === "1") return;
            confirmOkButton.dataset.processing = "1";
            closeConfirm(true);
        });
    }
    if (confirmCancelButton) {
        confirmCancelButton.addEventListener("click", function() {
            closeConfirm(false);
        });
    }
    if (confirmOverlay) {
        confirmOverlay.addEventListener("click", function(event) {
            if (event.target === confirmOverlay) {
                closeConfirm(false);
            }
        });
    }

    var forms = document.querySelectorAll("form[data-dup-form]");
    forms.forEach(function(form) {
        var primaryInput = form.querySelector(".dup-primary-input");
        var duplicateInput = form.querySelector(".dup-duplicate-input");
        var selectedLabel = form.querySelector("[data-selected-label]");
        var choicePanels = Array.prototype.slice.call(form.querySelectorAll(".dup-choice-panel"));
        var formError = form.querySelector(".dup-form-error");
        if (!primaryInput || !duplicateInput) {
            return;
        }

        function applySelection(primaryId, duplicateId) {
            primaryInput.value = String(primaryId || "");
            duplicateInput.value = String(duplicateId || "");
            choicePanels.forEach(function(panel) {
                var isSelected = panel.dataset.primaryId === String(primaryId);
                panel.classList.toggle("is-selected", isSelected);
            });
            if (selectedLabel) {
                var selectedPanel = null;
                for (var i = 0; i < choicePanels.length; i += 1) {
                    if (choicePanels[i].dataset.primaryId === String(primaryId)) {
                        selectedPanel = choicePanels[i];
                        break;
                    }
                }
                selectedLabel.textContent = selectedPanel ? (selectedPanel.dataset.primaryName || "") : "未選択";
            }
        }

        function selectFromPanel(panel) {
            if (!panel) return;
            var nextPrimaryId = panel.dataset.primaryId;
            var nextDuplicateId = panel.dataset.duplicateId;
            if (!nextPrimaryId || !nextDuplicateId) {
                return;
            }
            applySelection(nextPrimaryId, nextDuplicateId);
        }

        choicePanels.forEach(function(panel) {
            panel.addEventListener("pointerup", function(event) {
                event.preventDefault();
                selectFromPanel(panel);
            });
            panel.addEventListener("click", function() {
                selectFromPanel(panel);
            });
        });

        form.addEventListener("submit", function(event) {
            event.preventDefault();
            if (form.dataset.submitting === "1") return;
            if (formError) formError.textContent = "";

            if (!primaryInput.value || !duplicateInput.value) {
                if (formError) formError.textContent = "残す候補を選択してください。";
                return;
            }
            if (primaryInput.value === duplicateInput.value) {
                if (formError) formError.textContent = "残す場所と統合する場所が同じです。";
                return;
            }

            openConfirm("統合すると元に戻せません。実行しますか？").then(function(confirmed) {
                if (confirmOkButton) confirmOkButton.dataset.processing = "";
                if (!confirmed) return;
                form.dataset.submitting = "1";
                var submitButton = form.querySelector("button[type='submit'], input[type='submit']");
                if (submitButton) submitButton.disabled = true;
                if (window.MapAdminLoading && typeof window.MapAdminLoading.show === "function") {
                    window.MapAdminLoading.show("読み込み中");
                }
                form.submit();
            });
        });

        applySelection("", "");
    });
});
