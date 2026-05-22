import time

from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError

from map_app.cache_keys import (
    MAP_PAGE_CACHE_KEY,
    MAP_PAGE_RENDER_LOCK_KEY,
    MAP_PAGE_STALE_CACHE_KEY,
)


def get_unfiltered_map_page_html(render_func):
    cached_html = cache.get(MAP_PAGE_CACHE_KEY)
    if cached_html:
        return {"status": "cache_hit", "html": cached_html, "performance_count": None}

    stale_html = cache.get(MAP_PAGE_STALE_CACHE_KEY)
    if stale_html:
        return {"status": "stale_hit", "html": stale_html, "performance_count": None}

    lock_seconds = max(30, int(getattr(settings, "MAP_PAGE_RENDER_LOCK_SECONDS", 900)))
    if not cache.add(MAP_PAGE_RENDER_LOCK_KEY, "1", timeout=lock_seconds):
        # Another worker is generating. Wait briefly and reuse fresh/stale if available.
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            time.sleep(0.2)
            cached_html = cache.get(MAP_PAGE_CACHE_KEY)
            if cached_html:
                return {"status": "cache_wait_hit", "html": cached_html, "performance_count": None}
            stale_html = cache.get(MAP_PAGE_STALE_CACHE_KEY)
            if stale_html:
                return {"status": "cache_wait_stale", "html": stale_html, "performance_count": None}
        return {"status": "cache_wait_timeout", "html": None, "performance_count": None}

    try:
        rendered = render_func()
        html_string = rendered["html"]
        cache.set(MAP_PAGE_CACHE_KEY, html_string, settings.MAP_PAGE_CACHE_TIMEOUT_SECONDS)
        cache.set(
            MAP_PAGE_STALE_CACHE_KEY,
            html_string,
            getattr(settings, "MAP_PAGE_STALE_CACHE_TIMEOUT_SECONDS", 1800),
        )
        return {
            "status": "cache_miss",
            "html": html_string,
            "performance_count": rendered.get("performance_count"),
        }
    except DatabaseError:
        return {"status": "db_error", "html": None, "performance_count": None}
    finally:
        cache.delete(MAP_PAGE_RENDER_LOCK_KEY)
