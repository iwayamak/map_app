import os


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def require_redis_url_for_production(redis_url, *, debug, is_test):
    if not redis_url and not debug and not is_test:
        raise RuntimeError(
            "REDIS_URL must be set when DEBUG=False to avoid per-process cache fragmentation"
        )
