import hashlib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static

MAP_BUILD_VERSION = "20260608-8"
STATIC_PREFIX = getattr(settings, "MAP_APP_STATIC_PREFIX", "map_app").strip("/") or "map_app"
CACHE_KEY_NAMESPACE = getattr(settings, "MAP_APP_CACHE_KEY_NAMESPACE", "map_app").strip() or "map_app"

MAP_CSS_ASSET_PATHS = (
    f"{STATIC_PREFIX}/css/loading.css",
    f"{STATIC_PREFIX}/css/styles.css",
    f"{STATIC_PREFIX}/css/modal.css",
    f"{STATIC_PREFIX}/css/map_header_layout.css",
    f"{STATIC_PREFIX}/css/map_header_state.css",
    f"{STATIC_PREFIX}/css/map_header_interaction.css",
    f"{STATIC_PREFIX}/css/panels.css",
)

MAP_JS_ASSET_PATHS = (
    f"{STATIC_PREFIX}/js/map_marker_identity.js",
    f"{STATIC_PREFIX}/js/map_cluster_focus.js",
    f"{STATIC_PREFIX}/js/map_stability.js",
    f"{STATIC_PREFIX}/js/map_bootstrap.js",
    f"{STATIC_PREFIX}/js/map.js",
    f"{STATIC_PREFIX}/js/map_detail_modal_ui.js",
    f"{STATIC_PREFIX}/js/map_image_modal_ui.js",
    f"{STATIC_PREFIX}/js/loading_spinner.js",
    f"{STATIC_PREFIX}/js/map_modal_render.js",
    f"{STATIC_PREFIX}/js/map_modal_data.js",
    f"{STATIC_PREFIX}/js/map_modal.js",
    f"{STATIC_PREFIX}/js/map_zoom_controls.js",
    f"{STATIC_PREFIX}/js/map_marker_navigation.js",
    f"{STATIC_PREFIX}/js/map_layout.js",
    f"{STATIC_PREFIX}/js/map_controls.js",
    f"{STATIC_PREFIX}/js/map_search_utils.js",
    f"{STATIC_PREFIX}/js/map_search_contract.js",
    f"{STATIC_PREFIX}/js/map_search_store.js",
    f"{STATIC_PREFIX}/js/map_search_state.js",
    f"{STATIC_PREFIX}/js/map_search_tag_panel_ui.js",
    f"{STATIC_PREFIX}/js/map_search_summary_ui.js",
    f"{STATIC_PREFIX}/js/map_search_header_ui.js",
    f"{STATIC_PREFIX}/js/map_search_url_sync.js",
    f"{STATIC_PREFIX}/js/map_search_events.js",
    f"{STATIC_PREFIX}/js/map_search_api.js",
    f"{STATIC_PREFIX}/js/map_search.js",
    f"{STATIC_PREFIX}/js/map_search_actions.js",
    f"{STATIC_PREFIX}/js/page_loading.js",
    f"{STATIC_PREFIX}/js/ui_panels.js",
    f"{STATIC_PREFIX}/js/statistics_store.js",
    f"{STATIC_PREFIX}/js/statistics_dom_ui.js",
    f"{STATIC_PREFIX}/js/statistics_chart_ui.js",
    f"{STATIC_PREFIX}/js/statistics_panel.js",
)

MAP_PAGE_ASSET_PATHS = MAP_JS_ASSET_PATHS + MAP_CSS_ASSET_PATHS


def map_asset_url(path):
    return f"{static(path)}?v={MAP_BUILD_VERSION}"


def map_css_link_tags():
    return "\n".join(
        f'    <link rel="stylesheet" href="{map_asset_url(path)}" />'
        for path in MAP_CSS_ASSET_PATHS
    )


def map_js_script_tags():
    return "\n".join(
        f'    <script src="{map_asset_url(path)}"></script>'
        for path in MAP_JS_ASSET_PATHS
    )


def _map_cache_version_token():
    resolved_assets = []
    for path in MAP_PAGE_ASSET_PATHS:
        try:
            resolved_assets.append(static(path))
        except (ValueError, ImproperlyConfigured):
            resolved_assets.append(path)

    token = "|".join([MAP_BUILD_VERSION] + resolved_assets)
    return hashlib.sha1(token.encode("utf-8")).hexdigest()[:12]


def map_cache_key(name):
    return f"{CACHE_KEY_NAMESPACE}:{name}:{_map_cache_version_token()}"
