from map_app.domain import map_cache_key

MAP_PAGE_CACHE_KEY = map_cache_key("map_page_html")
MAP_PAGE_STALE_CACHE_KEY = map_cache_key("map_page_html_stale")
MAP_FILTERED_PAGE_CACHE_KEY_PREFIX = map_cache_key("map_page_filtered")
MAP_SEARCH_API_CACHE_KEY_PREFIX = map_cache_key("map_search_api")
MAP_PAGE_WARMUP_LOCK_KEY = map_cache_key("map_page_warmup_lock")
MAP_PAGE_WARMUP_PENDING_KEY = map_cache_key("map_page_warmup_pending")
MAP_PAGE_RENDER_LOCK_KEY = map_cache_key("map_page_render_lock")
VIDEO_PROCESSING_WAKE_KEY = map_cache_key("video_processing_wake")
