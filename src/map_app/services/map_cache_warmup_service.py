import logging
import os
import subprocess
import sys
import threading

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db import close_old_connections
from django.db.utils import DatabaseError

from map_app.cache_keys import (
    MAP_PAGE_CACHE_KEY,
    MAP_PAGE_STALE_CACHE_KEY,
    MAP_PAGE_WARMUP_LOCK_KEY,
    MAP_PAGE_WARMUP_PENDING_KEY,
)
from map_app.services.map_page_service import render_map_page_html

logger = logging.getLogger(__name__)


def _warm_map_cache(reason):
    lock_timeout = max(10, int(getattr(settings, "MAP_CACHE_WARMUP_LOCK_SECONDS", 120)))
    if not cache.add(MAP_PAGE_WARMUP_LOCK_KEY, "1", timeout=lock_timeout):
        logger.info("map_cache_warmup skipped reason=%s lock=busy", reason)
        return

    close_old_connections()
    try:
        rendered = render_map_page_html(AnonymousUser())
        cache.set(MAP_PAGE_CACHE_KEY, rendered["html"], settings.MAP_PAGE_CACHE_TIMEOUT_SECONDS)
        cache.set(
            MAP_PAGE_STALE_CACHE_KEY,
            rendered["html"],
            getattr(settings, "MAP_PAGE_STALE_CACHE_TIMEOUT_SECONDS", 1800),
        )
        logger.info(
            "map_cache_warmup done reason=%s performances=%s",
            reason,
            rendered["performance_count"],
        )
    except (DatabaseError, AttributeError, ValueError, TypeError, OSError, ConnectionError, TimeoutError):
        logger.exception("map_cache_warmup failed reason=%s", reason)
    finally:
        cache.delete(MAP_PAGE_WARMUP_LOCK_KEY)
        close_old_connections()


def warm_map_cache_now(reason="manual"):
    _warm_map_cache(reason)
    return True


def _resolve_warmup_mode():
    configured_mode = str(getattr(settings, "MAP_CACHE_WARMUP_MODE", "") or "").strip().lower()
    if configured_mode in {"sync", "thread", "command"}:
        return configured_mode

    if getattr(settings, "MAP_CACHE_WARMUP_THREAD_MODE", False):
        return "thread"
    return "sync"


def _run_warmup_command(reason):
    command = [sys.executable, "manage.py", "warm_map_cache", "--reason", reason]
    subprocess.Popen(
        command,
        cwd=str(settings.BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy(),
    )
    return True


def schedule_map_cache_warmup(reason="data_change"):
    if not getattr(settings, "MAP_CACHE_WARMUP_ENABLED", True):
        return False

    debounce_seconds = max(1, int(getattr(settings, "MAP_CACHE_WARMUP_DEBOUNCE_SECONDS", 3)))
    if not cache.add(MAP_PAGE_WARMUP_PENDING_KEY, "1", timeout=debounce_seconds):
        return False

    mode = _resolve_warmup_mode()
    if mode == "thread":
        threading.Thread(target=_warm_map_cache, args=(reason,), daemon=True).start()
        return True
    if mode == "command":
        try:
            return _run_warmup_command(reason)
        except (AttributeError, ValueError, TypeError, OSError):
            logger.exception("map_cache_warmup command launch failed reason=%s", reason)
            return False

    _warm_map_cache(reason)
    return True
