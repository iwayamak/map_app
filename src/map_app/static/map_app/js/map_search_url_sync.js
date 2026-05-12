(function(global) {
    function createUrlSync(config, utils) {
        function replaceFromParams(params) {
            utils.replaceBrowserUrl(params);
        }

        function consumeLegacyKeepOpenParam(onKeepOpen) {
            var params = new URLSearchParams(window.location.search);
            if (params.get(config.legacyKeepOpenParam) !== "1") {
                return;
            }

            if (typeof onKeepOpen === "function") {
                onKeepOpen();
            }
            params.delete(config.legacyKeepOpenParam);
            replaceFromParams(params);
        }

        return {
            replaceFromParams: replaceFromParams,
            consumeLegacyKeepOpenParam: consumeLegacyKeepOpenParam,
        };
    }

    global.MapSearchUrlSync = {
        create: createUrlSync,
    };
})(window);
