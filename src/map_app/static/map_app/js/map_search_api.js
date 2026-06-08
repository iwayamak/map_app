(function(global) {
    function createSearchApi(config, searchState, store, hooks) {
        var contract = global.MapSearchContract;
        if (!contract || typeof contract.validateMapSearchPayload !== "function") {
            throw new Error("MapSearchContract is not loaded.");
        }

        function run() {
            var requestToken = store.nextRequestToken();
            var params = searchState.buildSearchParams();
            var slowRequestTimer = null;

            if (global.MapAppPageLoading && typeof global.MapAppPageLoading.show === "function") {
                slowRequestTimer = setTimeout(function() {
                    if (!store.isLatestRequestToken(requestToken)) return;
                    global.MapAppPageLoading.show({
                        title: "読み込み中",
                        copy: ""
                    });
                }, 450);
            }

            function clearSlowRequestLoading() {
                if (slowRequestTimer) {
                    clearTimeout(slowRequestTimer);
                    slowRequestTimer = null;
                }
                if (global.MapAppPageLoading && typeof global.MapAppPageLoading.hide === "function") {
                    global.MapAppPageLoading.hide();
                }
            }

            var activeController = store.getActiveRequestController();
            if (activeController) {
                activeController.abort();
            }
            var nextController = new AbortController();
            store.setActiveRequestController(nextController);

            fetch(config.searchApiUrl + "?" + params.toString(), {
                method: "GET",
                headers: { "X-Requested-With": "XMLHttpRequest" },
                signal: nextController.signal,
            })
                .then(function(response) {
                    if (!response.ok) {
                        throw new Error("Failed to fetch search results");
                    }
                    return response.json();
                })
                .then(function(payload) {
                    if (!store.isLatestRequestToken(requestToken)) return;
                    contract.validateMapSearchPayload(payload);
                    clearSlowRequestLoading();
                    hooks.onSuccess(payload, params);
                })
                .catch(function(error) {
                    if (!store.isLatestRequestToken(requestToken)) return;
                    clearSlowRequestLoading();
                    if (error && error.name === "AbortError") return;
                    if (hooks.onError) hooks.onError(error);
                });
        }

        return {
            run: run,
        };
    }

    global.MapSearchApi = {
        create: createSearchApi,
    };
})(window);
