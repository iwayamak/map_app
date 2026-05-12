(function(global) {
    function createSearchApi(config, searchState, store, hooks) {
        var contract = global.MapSearchContract;
        if (!contract || typeof contract.validateMapSearchPayload !== "function") {
            throw new Error("MapSearchContract is not loaded.");
        }

        function run() {
            var requestToken = store.nextRequestToken();
            var params = searchState.buildSearchParams();

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
                    hooks.onSuccess(payload, params);
                })
                .catch(function(error) {
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
