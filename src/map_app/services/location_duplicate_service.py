import math
import unicodedata
from difflib import SequenceMatcher

from django.db import transaction
from django.db.models import Count, Max

from map_app.domain import get_activity_log_model, get_location_model, get_location_photo_model


def normalize_location_name(name):
    text = unicodedata.normalize("NFKC", (name or "").strip().lower())
    filtered = []
    for char in text:
        if char.isalnum():
            filtered.append(char)
    return "".join(filtered)


def haversine_distance_km(lat1, lng1, lat2, lng2):
    radius_km = 6371.0088
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return radius_km * 2 * math.asin(math.sqrt(a))


def _normalize_score(value, *, minimum, maximum):
    if maximum <= minimum:
        return 0.0
    bounded = max(minimum, min(maximum, value))
    return (bounded - minimum) / (maximum - minimum)


def _distance_confidence(distance_km, *, distance_threshold_km):
    if distance_threshold_km <= 0:
        return 0.0
    if distance_km >= distance_threshold_km:
        return 0.0
    return 1.0 - (distance_km / distance_threshold_km)


def _tag_overlap_ratio(left_tags, right_tags):
    if not left_tags or not right_tags:
        return 0.0
    left_set = set(left_tags)
    right_set = set(right_tags)
    union = left_set | right_set
    if not union:
        return 0.0
    return len(left_set & right_set) / len(union)


def _location_detail_score(location):
    performance_count = getattr(location, "_dup_performance_count", 0) or 0
    photo_count = getattr(location, "_dup_photo_count", 0) or 0
    has_image = 1 if getattr(location, "image", None) else 0
    tag_count = len(getattr(location, "_dup_tags", ()))
    return (performance_count * 3) + (photo_count * 2) + tag_count + has_image


def _candidate_confidence(*, name_similarity, distance_km, distance_threshold_km, tag_overlap_ratio, exact_name_match):
    name_component = _normalize_score(name_similarity, minimum=0.55, maximum=1.0) * 45.0
    distance_component = _distance_confidence(distance_km, distance_threshold_km=distance_threshold_km) * 35.0
    tag_component = tag_overlap_ratio * 15.0
    exact_bonus = 5.0 if exact_name_match else 0.0
    return round(min(100.0, name_component + distance_component + tag_component + exact_bonus), 1)


def _choose_merge_direction(left, right):
    left_score = _location_detail_score(left)
    right_score = _location_detail_score(right)
    if left_score == right_score:
        primary = left if left.id < right.id else right
        duplicate = right if primary is left else left
    else:
        primary = left if left_score > right_score else right
        duplicate = right if primary is left else left
    return primary, duplicate, left_score, right_score


def detect_location_duplicates(
    locations,
    *,
    name_similarity_threshold=0.88,
    distance_threshold_km=0.35,
    nearby_threshold_km=0.05,
):
    ActivityLog = get_activity_log_model()
    LocationPhoto = get_location_photo_model()
    location_list = list(locations)
    results = []
    max_distance_km = max(distance_threshold_km, nearby_threshold_km)
    lat_window_deg = max_distance_km / 111.0
    location_ids = [location.id for location in location_list]
    performance_counts = dict(
        ActivityLog.objects.filter(location_id__in=location_ids)
        .values("location_id")
        .annotate(count=Count("id"))
        .values_list("location_id", "count")
    )
    photo_counts = dict(
        LocationPhoto.objects.filter(location_id__in=location_ids)
        .values("location_id")
        .annotate(count=Count("id"))
        .values_list("location_id", "count")
    )

    for location in location_list:
        location._dup_tags = tuple(sorted(tag.name for tag in location.tags.all()))
        location._dup_norm_name = normalize_location_name(location.name)
        location._dup_performance_count = getattr(location, "performance_count", None)
        if location._dup_performance_count is None:
            location._dup_performance_count = performance_counts.get(location.id, 0)
        location._dup_photo_count = getattr(location, "photo_count", None)
        if location._dup_photo_count is None:
            location._dup_photo_count = photo_counts.get(location.id, 0)

    sorted_locations = sorted(location_list, key=lambda item: item.latitude)
    for i, left in enumerate(sorted_locations):
        left_norm = left._dup_norm_name
        for right in sorted_locations[i + 1:]:
            if (right.latitude - left.latitude) > lat_window_deg:
                break

            mean_lat = (left.latitude + right.latitude) / 2.0
            cos_value = max(0.173648, abs(math.cos(math.radians(mean_lat))))
            lng_window_deg = max_distance_km / (111.0 * cos_value)
            if abs(right.longitude - left.longitude) > lng_window_deg:
                continue

            right_norm = right._dup_norm_name
            if not left_norm or not right_norm:
                continue

            name_similarity = SequenceMatcher(None, left_norm, right_norm).ratio()
            distance_km = haversine_distance_km(
                left.latitude,
                left.longitude,
                right.latitude,
                right.longitude,
            )

            name_match = left_norm == right_norm or name_similarity >= name_similarity_threshold
            close_match = distance_km <= nearby_threshold_km
            same_area = distance_km <= distance_threshold_km
            tag_overlap_ratio = _tag_overlap_ratio(left._dup_tags, right._dup_tags)
            confidence_score = _candidate_confidence(
                name_similarity=name_similarity,
                distance_km=distance_km,
                distance_threshold_km=distance_threshold_km,
                tag_overlap_ratio=tag_overlap_ratio,
                exact_name_match=(left_norm == right_norm),
            )

            likely_duplicate = (name_match and same_area) or close_match or confidence_score >= 68.0
            if likely_duplicate:
                primary, duplicate, left_detail_score, right_detail_score = _choose_merge_direction(left, right)
                detail_scores = {left.id: left_detail_score, right.id: right_detail_score}
                total_detail_score = max(1, left_detail_score + right_detail_score)
                results.append(
                    {
                        "primary": primary,
                        "duplicate": duplicate,
                        "distance_km": round(distance_km, 4),
                        "name_similarity": round(name_similarity, 4),
                        "name_similarity_percent": round(name_similarity * 100, 1),
                        "tag_overlap_ratio": round(tag_overlap_ratio, 4),
                        "tag_overlap_percent": round(tag_overlap_ratio * 100, 1),
                        "confidence_score": confidence_score,
                        "primary_detail_score": detail_scores[primary.id],
                        "duplicate_detail_score": detail_scores[duplicate.id],
                        "primary_recommend_percent": round((detail_scores[primary.id] / total_detail_score) * 100, 1),
                        "duplicate_recommend_percent": round((detail_scores[duplicate.id] / total_detail_score) * 100, 1),
                        "location_choices": [
                            {"id": left.id, "name": left.name},
                            {"id": right.id, "name": right.name},
                        ],
                    }
                )

    return sorted(
        results,
        key=lambda item: (-item["confidence_score"], item["distance_km"], -item["name_similarity"], item["primary"].id, item["duplicate"].id),
    )


@transaction.atomic
def merge_locations(*, primary_id, duplicate_id):
    ActivityLog = get_activity_log_model()
    Location = get_location_model()
    LocationPhoto = get_location_photo_model()
    if primary_id == duplicate_id:
        raise ValueError("同じ場所は統合できません")

    primary = Location.objects.select_for_update().get(pk=primary_id)
    duplicate = Location.objects.select_for_update().get(pk=duplicate_id)

    def _append_legacy_image_as_photo(location):
        if not location.image:
            return
        image_name = str(location.image)
        already_exists = LocationPhoto.objects.filter(location=primary, image=image_name).exists()
        if already_exists:
            return
        max_order = (
            LocationPhoto.objects.filter(location=primary).aggregate(max_order=Max("order")).get("max_order") or 0
        )
        LocationPhoto.objects.create(
            location=primary,
            image=image_name,
            order=max_order + 1,
        )

    _append_legacy_image_as_photo(primary)
    _append_legacy_image_as_photo(duplicate)

    ActivityLog.objects.filter(location=duplicate).update(location=primary)
    LocationPhoto.objects.filter(location=duplicate).update(location=primary)
    primary.tags.add(*duplicate.tags.all())

    if not primary.image and duplicate.image:
        primary.image = duplicate.image
        primary.save(update_fields=["image"])

    duplicate.delete()
    return primary
