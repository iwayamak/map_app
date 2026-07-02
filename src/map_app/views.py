import hashlib
import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from map_app.cache_keys import (
    MAP_FILTERED_CACHE_VERSION_KEY,
    MAP_FILTERED_PAGE_CACHE_KEY_PREFIX,
    MAP_PAGE_CACHE_KEY,
    MAP_PAGE_STALE_CACHE_KEY,
    MAP_SEARCH_API_CACHE_KEY_PREFIX,
    MAP_SEARCH_API_CACHE_VERSION_KEY,
)
from map_app.contracts.map_search_contract import validate_map_search_payload
from map_app.domain import get_activity_log_model
from map_app.services.activity_modal_service import (
    build_activity_modal_payload,
    build_location_modal_payload,
)
from map_app.services.healthcheck_service import run_health_checks
from map_app.services.map_cache_warmup_service import schedule_map_cache_warmup
from map_app.services.map_page_cache_service import get_unfiltered_map_page_html
from map_app.services.map_page_service import build_map_search_payload, render_map_page_html
from map_app.services.public_activity_service import build_recent_activity_payload
from map_app.services.site_context_service import load_site_context
from map_app.services.video_query_service import build_interleaved_video_rows, get_published_videos_queryset

logger = logging.getLogger(__name__)


def _get_cache_version(version_key):
    value = cache.get(version_key)
    if isinstance(value, int) and value > 0:
        return value
    cache.set(version_key, 1, None)
    return 1


def _build_search_cache_key(prefix, search_query, selected_tags, version_key):
    normalized_query = (search_query or "").strip()
    normalized_tags = sorted([tag.strip() for tag in (selected_tags or []) if tag and tag.strip()])
    cache_version = _get_cache_version(version_key)
    material = f"v={cache_version}|q={normalized_query}|tags={','.join(normalized_tags)}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}:{digest}"


def _is_unfiltered_search_cache_fresh(cached_payload, search_query, selected_tags):
    if search_query or selected_tags:
        return True
    if not isinstance(cached_payload, dict):
        return False
    summary = cached_payload.get("summary")
    if not isinstance(summary, dict):
        return False
    cached_total = summary.get("total_activity_logs")
    if not isinstance(cached_total, int):
        return False
    ActivityLog = get_activity_log_model()
    return cached_total == ActivityLog.objects.count()


def healthz_view(request):
    health = run_health_checks()
    return JsonResponse(
        {
            "status": health["status"],
            "checks": health["checks"],
            "details": health["details"],
            "elapsed_ms": health["elapsed_ms"],
        },
        status=health["http_status"],
    )


def _extract_search_params(request):
    search_query = (request.GET.get("q") or "").strip()
    selected_tags = [tag.strip() for tag in request.GET.getlist("tags") if tag and tag.strip()]
    legacy_tag = (request.GET.get("tag") or "").strip()
    if legacy_tag and legacy_tag not in selected_tags:
        selected_tags.append(legacy_tag)
    return search_query, selected_tags


def map_view(request):
    started_at = time.perf_counter()
    search_query, selected_tags = _extract_search_params(request)
    has_filters = bool(search_query or selected_tags)

    if has_filters:
        try:
            filtered_cache_key = _build_search_cache_key(
                MAP_FILTERED_PAGE_CACHE_KEY_PREFIX,
                search_query=search_query,
                selected_tags=selected_tags,
                version_key=MAP_FILTERED_CACHE_VERSION_KEY,
            )
            cached_filtered_html = None
            if settings.MAP_FILTERED_CACHE_TIMEOUT_SECONDS > 0:
                cached_filtered_html = cache.get(filtered_cache_key)
            if cached_filtered_html:
                elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                level = logger.warning if elapsed_ms >= settings.API_SLOW_LOG_THRESHOLD_MS else logger.info
                level(
                    "map_view filtered_cache_hit elapsed_ms=%s q=%s tags=%s cache_key=%s",
                    elapsed_ms,
                    search_query,
                    ",".join(selected_tags),
                    filtered_cache_key,
                )
                return HttpResponse(cached_filtered_html)

            rendered = render_map_page_html(
                request.user,
                search_query=search_query,
                selected_tags=selected_tags,
            )
            if settings.MAP_FILTERED_CACHE_TIMEOUT_SECONDS > 0:
                cache.set(
                    filtered_cache_key,
                    rendered["html"],
                    settings.MAP_FILTERED_CACHE_TIMEOUT_SECONDS,
                )
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            level = logger.warning if elapsed_ms >= settings.API_SLOW_LOG_THRESHOLD_MS else logger.info
            level(
                "map_view filtered_cache_miss elapsed_ms=%s q=%s tags=%s records=%s cache_timeout_seconds=%s",
                elapsed_ms,
                search_query,
                ",".join(selected_tags),
                rendered["record_count"],
                settings.MAP_FILTERED_CACHE_TIMEOUT_SECONDS,
            )
            return HttpResponse(rendered["html"])
        except (ValueError, ValidationError) as exc:
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            logger.warning(
                "map_view filtered invalid_request elapsed_ms=%s q=%s tags=%s error=%s",
                elapsed_ms,
                search_query,
                ",".join(selected_tags),
                str(exc),
            )
            return HttpResponse("Invalid search parameters.", status=400)
        except DatabaseError:
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            logger.exception(
                "map_view filtered db_error elapsed_ms=%s q=%s tags=%s",
                elapsed_ms,
                search_query,
                ",".join(selected_tags),
            )
            return HttpResponse("Service temporarily unavailable.", status=503)

    result = get_unfiltered_map_page_html(
        lambda: render_map_page_html(request.user, search_query="", selected_tags=[])
    )
    status = result["status"]
    html = result["html"]
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    level = logger.warning if elapsed_ms >= settings.API_SLOW_LOG_THRESHOLD_MS else logger.info

    if status == "cache_hit":
        level("map_view cache_hit elapsed_ms=%s cache_key=%s", elapsed_ms, MAP_PAGE_CACHE_KEY)
        return HttpResponse(html)
    if status in {"stale_hit", "cache_wait_stale"}:
        schedule_map_cache_warmup(reason="stale_served")
        level("map_view stale_hit elapsed_ms=%s cache_key=%s", elapsed_ms, MAP_PAGE_STALE_CACHE_KEY)
        return HttpResponse(html)
    if status == "cache_wait_hit":
        level("map_view cache_hit elapsed_ms=%s cache_key=%s", elapsed_ms, MAP_PAGE_CACHE_KEY)
        return HttpResponse(html)
    if status == "cache_miss":
        level(
            "map_view cache_miss elapsed_ms=%s cache_timeout_seconds=%s records=%s",
            elapsed_ms,
            settings.MAP_PAGE_CACHE_TIMEOUT_SECONDS,
            result["record_count"],
        )
        return HttpResponse(html)

    if status == "db_error":
        logger.exception("map_view db_error elapsed_ms=%s", elapsed_ms)
        return HttpResponse("Service temporarily unavailable.", status=503)
    logger.warning("map_view cache_wait_timeout elapsed_ms=%s", elapsed_ms)
    return HttpResponse("Service temporarily unavailable.", status=503)


def activity_modal_view(request, activity_id):
    started_at = time.perf_counter()
    try:
        activity_payload = build_activity_modal_payload(activity_id)
        response = JsonResponse({"activity": activity_payload})
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        level = logger.warning if elapsed_ms >= settings.API_SLOW_LOG_THRESHOLD_MS else logger.info
        level(
            "activity_modal_view success elapsed_ms=%s activity_id=%s photos=%s items=%s",
            elapsed_ms,
            activity_id,
            len(activity_payload["photo_assets"]),
            len(activity_payload["activity_items"]),
        )
        return response
    except Http404:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            "activity_modal_view not_found elapsed_ms=%s activity_id=%s",
            elapsed_ms,
            activity_id,
        )
        return JsonResponse({"error": "Activity not found."}, status=404)
    except DatabaseError:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.exception(
            "activity_modal_view db_error elapsed_ms=%s activity_id=%s",
            elapsed_ms,
            activity_id,
        )
        return JsonResponse({"error": "Service temporarily unavailable."}, status=503)


def location_modal_view(request, location_id):
    started_at = time.perf_counter()
    try:
        location_payload = build_location_modal_payload(location_id)
        response = JsonResponse({"activity": location_payload})
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        level = logger.warning if elapsed_ms >= settings.API_SLOW_LOG_THRESHOLD_MS else logger.info
        level(
            "location_modal_view success elapsed_ms=%s location_id=%s photos=%s tags=%s",
            elapsed_ms,
            location_id,
            len(location_payload["photo_assets"]),
            len(location_payload["tags"]),
        )
        return response
    except Http404:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            "location_modal_view not_found elapsed_ms=%s location_id=%s",
            elapsed_ms,
            location_id,
        )
        return JsonResponse({"error": "Location not found."}, status=404)
    except DatabaseError:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.exception(
            "location_modal_view db_error elapsed_ms=%s location_id=%s",
            elapsed_ms,
            location_id,
        )
        return JsonResponse({"error": "Service temporarily unavailable."}, status=503)


def map_search_api_view(request):
    started_at = time.perf_counter()
    search_query, selected_tags = _extract_search_params(request)

    try:
        search_cache_key = _build_search_cache_key(
            MAP_SEARCH_API_CACHE_KEY_PREFIX,
            search_query=search_query,
            selected_tags=selected_tags,
            version_key=MAP_SEARCH_API_CACHE_VERSION_KEY,
        )
        cached_payload = None
        if settings.MAP_SEARCH_API_CACHE_TIMEOUT_SECONDS > 0:
            cached_payload = cache.get(search_cache_key)
        if cached_payload:
            if _is_unfiltered_search_cache_fresh(cached_payload, search_query, selected_tags):
                elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                level = logger.warning if elapsed_ms >= settings.API_SLOW_LOG_THRESHOLD_MS else logger.info
                level(
                    "map_search_api_view cache_hit elapsed_ms=%s q=%s tags=%s cache_key=%s markers=%s",
                    elapsed_ms,
                    search_query,
                    ",".join(selected_tags),
                    search_cache_key,
                    len(cached_payload.get("markers", [])),
                )
                return JsonResponse(cached_payload)
            cache.delete(search_cache_key)
            logger.info(
                "map_search_api_view stale_cache_deleted q=%s tags=%s cache_key=%s",
                search_query,
                ",".join(selected_tags),
                search_cache_key,
            )

        payload = build_map_search_payload(search_query=search_query, selected_tags=selected_tags)
        validate_map_search_payload(payload)
        if settings.MAP_SEARCH_API_CACHE_TIMEOUT_SECONDS > 0:
            cache.set(search_cache_key, payload, settings.MAP_SEARCH_API_CACHE_TIMEOUT_SECONDS)
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        level = logger.warning if elapsed_ms >= settings.API_SLOW_LOG_THRESHOLD_MS else logger.info
        level(
            "map_search_api_view cache_miss elapsed_ms=%s q=%s tags=%s markers=%s cache_timeout_seconds=%s",
            elapsed_ms,
            search_query,
            ",".join(selected_tags),
            len(payload["markers"]),
            settings.MAP_SEARCH_API_CACHE_TIMEOUT_SECONDS,
        )
        return JsonResponse(payload)
    except (ValueError, ValidationError) as exc:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.warning(
            "map_search_api_view invalid_request elapsed_ms=%s q=%s tags=%s error=%s",
            elapsed_ms,
            search_query,
            ",".join(selected_tags),
            str(exc),
        )
        return JsonResponse({"error": "Invalid search parameters."}, status=400)
    except DatabaseError:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.exception(
            "map_search_api_view db_error elapsed_ms=%s q=%s tags=%s",
            elapsed_ms,
            search_query,
            ",".join(selected_tags),
        )
        return JsonResponse({"error": "Service temporarily unavailable."}, status=503)


def public_recent_activities_view(request):
    try:
        limit = max(1, min(20, int(request.GET.get("limit", "5"))))
    except ValueError:
        return JsonResponse({"error": "Invalid limit."}, status=400)
    try:
        return JsonResponse(build_recent_activity_payload(request, limit=limit))
    except DatabaseError:
        logger.exception("public_recent_activities_view db_error")
        return JsonResponse({"error": "Service temporarily unavailable."}, status=503)


def video_library_view(request):
    site_settings, domain_terms = load_site_context()
    video_queryset = get_published_videos_queryset().order_by("-published_at", "-created_at")
    search_query = (request.GET.get("q") or "").strip()
    if search_query:
        video_queryset = video_queryset.filter(title__icontains=search_query)

    paginator = Paginator(video_queryset, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    videos = list(page_obj.object_list)
    video_rows_pc = build_interleaved_video_rows(
        videos,
        portrait_row_size=6,
        landscape_row_size=3,
        include_remainder=True,
    )
    video_rows_mobile = build_interleaved_video_rows(
        videos,
        portrait_row_size=2,
        landscape_row_size=1,
        include_remainder=True,
    )

    return render(
        request,
        "map_app/video_library.html",
        {
            "videos": videos,
            "video_rows_pc": video_rows_pc,
            "video_rows_mobile": video_rows_mobile,
            "page_obj": page_obj,
            "video_count": paginator.count,
            "search_query": search_query,
            "site_settings": site_settings,
            "domain_terms": domain_terms,
            "video_library_url": reverse(f"{getattr(settings, 'MAP_APP_URL_NAMESPACE', 'map_app')}:video_library"),
        },
    )


def video_detail_view(request, video_id):
    site_settings, domain_terms = load_site_context()
    video = get_published_videos_queryset().filter(id=video_id).first()
    if not video:
        raise Http404("Video not found.")

    related_videos = list(get_published_videos_queryset().exclude(id=video.id)[:8])
    related_video_rows = build_interleaved_video_rows(
        related_videos,
        portrait_row_size=3,
        landscape_row_size=1,
        include_remainder=True,
    )
    return render(
        request,
        "map_app/video_detail.html",
        {
            "video": video,
            "related_videos": related_videos,
            "related_video_rows": related_video_rows,
            "site_settings": site_settings,
            "domain_terms": domain_terms,
        },
    )


def video_short_detail_view(request, video_id):
    site_settings, domain_terms = load_site_context()
    video = get_published_videos_queryset().filter(id=video_id).first()
    if not video or not video.is_portrait_video:
        raise Http404("Video not found.")

    return render(
        request,
        "map_app/video_short_detail.html",
        {
            "video": video,
            "site_settings": site_settings,
            "domain_terms": domain_terms,
            "video_library_url": reverse(f"{getattr(settings, 'MAP_APP_URL_NAMESPACE', 'map_app')}:video_library"),
        },
    )
