import time

from django.core.cache import cache
from django.db import connection
from django.db.utils import DatabaseError


def run_health_checks(*, cache_backend=None, db_connection=None):
    cache_backend = cache if cache_backend is None else cache_backend
    db_connection = connection if db_connection is None else db_connection
    started_at = time.perf_counter()
    checks = {"db": "ok", "cache": "ok"}
    details = {}

    try:
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError as exc:
        checks["db"] = "error"
        details["db_error"] = str(exc)

    cache_key = "map_app:healthz:probe"
    try:
        cache_backend.set(cache_key, "ok", 5)
        if cache_backend.get(cache_key) != "ok":
            checks["cache"] = "error"
            details["cache_error"] = "cache roundtrip mismatch"
        details["cache_backend"] = cache_backend.__class__.__module__ + "." + cache_backend.__class__.__name__

        redis_client_factory = getattr(getattr(cache_backend, "_cache", None), "get_client", None)
        if callable(redis_client_factory):
            try:
                redis_client = redis_client_factory()
                redis_ok = bool(redis_client.ping())
                checks["redis"] = "ok" if redis_ok else "error"
                if not redis_ok:
                    details["redis_error"] = "redis ping returned false"
            except (AttributeError, ValueError, TypeError, OSError, ConnectionError, TimeoutError) as exc:
                checks["redis"] = "error"
                details["redis_error"] = str(exc)
        else:
            checks["redis"] = "not_configured"
    except (AttributeError, ValueError, TypeError, OSError, ConnectionError, TimeoutError) as exc:
        checks["cache"] = "error"
        checks["redis"] = "error"
        details["cache_error"] = str(exc)

    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    redis_ok = checks.get("redis") in {"ok", "not_configured"}
    is_ok = checks["db"] == "ok" and checks["cache"] == "ok" and redis_ok

    return {
        "status": "ok" if is_ok else "error",
        "checks": checks,
        "details": details,
        "elapsed_ms": elapsed_ms,
        "http_status": 200 if is_ok else 503,
    }
