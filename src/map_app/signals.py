import logging

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save

from map_app.cache_keys import (
    MAP_FILTERED_CACHE_VERSION_KEY,
    MAP_PAGE_CACHE_KEY,
    MAP_PAGE_STALE_CACHE_KEY,
    MAP_SEARCH_API_CACHE_VERSION_KEY,
    SITE_SETTINGS_CACHE_KEY,
    SITE_SETTINGS_DOMAIN_TERMS_CACHE_KEY,
)

logger = logging.getLogger(__name__)


def invalidate_site_context_cache():
    cache.delete(SITE_SETTINGS_CACHE_KEY)
    cache.delete(SITE_SETTINGS_DOMAIN_TERMS_CACHE_KEY)


def bump_search_cache_versions():
    for version_key in (MAP_FILTERED_CACHE_VERSION_KEY, MAP_SEARCH_API_CACHE_VERSION_KEY):
        try:
            cache.incr(version_key)
        except (AttributeError, ValueError, TypeError):
            cache.set(version_key, 2, None)


def invalidate_map_cache(*, preserve_stale=True):
    existing = cache.get(MAP_PAGE_CACHE_KEY)
    if preserve_stale and existing:
        cache.set(
            MAP_PAGE_STALE_CACHE_KEY,
            existing,
            timeout=getattr(settings, "MAP_PAGE_STALE_CACHE_TIMEOUT_SECONDS", 1800),
        )
    if not preserve_stale:
        cache.delete(MAP_PAGE_STALE_CACHE_KEY)
    cache.delete(MAP_PAGE_CACHE_KEY)
    bump_search_cache_versions()


def connect_map_cache_invalidation(
    *,
    site_settings_model,
    location_model,
    location_photo_model,
    activity_log_model,
    activity_log_item_model,
    activity_item_model,
    tag_model,
    schedule_map_cache_warmup,
    schedule_link_preview_cache_warmup,
):
    app_label = location_model._meta.app_label
    watched_models = (
        site_settings_model,
        location_model,
        location_photo_model,
        activity_log_model,
        activity_log_item_model,
        activity_item_model,
        tag_model,
    )

    def invalidate_cache_on_data_change(sender, **kwargs):
        if kwargs.get("raw"):
            return

        if sender is site_settings_model:
            invalidate_site_context_cache()
        preserve_stale = sender is not site_settings_model
        invalidate_map_cache(preserve_stale=preserve_stale)
        instance = kwargs.get("instance")

        def _on_commit_warmup():
            try:
                schedule_map_cache_warmup(reason=f"{sender.__name__}_updated")
            except (AttributeError, ValueError, TypeError, OSError, ConnectionError, TimeoutError):
                logger.exception("failed to schedule map cache warmup sender=%s", sender.__name__)
            if sender is location_model and instance and getattr(instance, "detail_note", "").strip():
                try:
                    schedule_link_preview_cache_warmup(instance.detail_note)
                except (AttributeError, ValueError, TypeError, OSError, ConnectionError, TimeoutError):
                    logger.exception("failed to schedule link preview warmup sender=%s", sender.__name__)

        transaction.on_commit(_on_commit_warmup)

    for model in watched_models:
        post_save.connect(
            invalidate_cache_on_data_change,
            sender=model,
            dispatch_uid=f"{app_label}:invalidate_cache:{model.__name__}:save",
        )
        post_delete.connect(
            invalidate_cache_on_data_change,
            sender=model,
            dispatch_uid=f"{app_label}:invalidate_cache:{model.__name__}:delete",
        )

    def invalidate_cache_on_location_tags_changed(sender, action, **kwargs):
        if action not in {"post_add", "post_remove", "post_clear"}:
            return

        invalidate_map_cache()

        def _on_commit_warmup():
            try:
                schedule_map_cache_warmup(reason=f"LocationTags_{action}")
            except (AttributeError, ValueError, TypeError, OSError, ConnectionError, TimeoutError):
                logger.exception("failed to schedule map cache warmup sender=Location.tags action=%s", action)

        transaction.on_commit(_on_commit_warmup)

    m2m_changed.connect(
        invalidate_cache_on_location_tags_changed,
        sender=location_model.tags.through,
        dispatch_uid=f"{app_label}:invalidate_cache:location_tags:m2m",
    )
