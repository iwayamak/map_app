import hashlib
import re
import sys

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from map_app.domain_terms import get_domain_term_bool


VIBRANT_TAG_COLORS = [
    "#2563eb", "#7c3aed", "#db2777", "#ea580c", "#ca8a04", "#059669", "#0f766e", "#0891b2",
    "#4f46e5", "#9333ea", "#c026d3", "#e11d48", "#dc2626", "#d97706", "#65a30d", "#16a34a",
    "#0d9488", "#0284c7", "#1d4ed8", "#6d28d9", "#9d174d", "#b45309", "#a16207", "#15803d",
    "#0f766e", "#0369a1", "#4338ca", "#8b5cf6", "#be185d", "#f43f5e", "#f59e0b", "#84cc16",
]


def get_model_default_domain_terms(model_cls):
    module = sys.modules.get(model_cls.__module__)
    default_domain_terms = getattr(module, "default_domain_terms", None)
    if default_domain_terms is None:
        return {}
    return default_domain_terms()


class SiteSettingsBehavior:
    @classmethod
    def clear_site_settings_cache(cls):
        from map_app.cache_keys import SITE_SETTINGS_CACHE_KEY, SITE_SETTINGS_DOMAIN_TERMS_CACHE_KEY

        cache.delete(SITE_SETTINGS_CACHE_KEY)
        cache.delete(SITE_SETTINGS_DOMAIN_TERMS_CACHE_KEY)

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def load_cached(cls):
        from map_app.cache_keys import SITE_SETTINGS_CACHE_KEY

        cached = cache.get(SITE_SETTINGS_CACHE_KEY)
        if cached is not None:
            return cached
        obj = cls.objects.filter(pk=1).first()
        if obj is None:
            obj = cls.objects.create(pk=1)
        cache.set(SITE_SETTINGS_CACHE_KEY, obj, timeout=300)
        return obj

    @classmethod
    def load_domain_terms_cached(cls):
        from map_app.cache_keys import SITE_SETTINGS_DOMAIN_TERMS_CACHE_KEY

        cached = cache.get(SITE_SETTINGS_DOMAIN_TERMS_CACHE_KEY)
        if isinstance(cached, dict):
            return cached
        terms = cls.load_cached().get_domain_terms()
        cache.set(SITE_SETTINGS_DOMAIN_TERMS_CACHE_KEY, terms, timeout=300)
        return terms

    def get_domain_terms(self):
        terms = get_model_default_domain_terms(type(self))
        current = self.domain_terms if isinstance(self.domain_terms, dict) else {}
        for key, value in current.items():
            if isinstance(value, str) and value.strip():
                terms[key] = value.strip()
            elif isinstance(value, dict) and isinstance(terms.get(key), dict):
                terms[key].update(value)
            elif value is not None and not isinstance(value, str):
                terms[key] = value
        terms["use_record_items"] = get_domain_term_bool(terms, "use_record_items", default=True)
        terms["show_video_library_menu"] = get_domain_term_bool(terms, "show_video_library_menu", default=True)
        terms["statistics_show_recent_item_title"] = get_domain_term_bool(
            terms,
            "statistics_show_recent_item_title",
            default=True,
        )
        modal_sections = terms.get("modal_sections")
        if not isinstance(modal_sections, dict):
            modal_sections = {}
        if not terms["use_record_items"]:
            modal_sections["records"] = False
        terms["modal_sections"] = modal_sections
        return terms


class TagBehavior:
    @staticmethod
    def _hex_to_rgb_tuple(hex_color):
        hex_value = (hex_color or "").lstrip("#")
        if len(hex_value) != 6:
            return (75, 85, 99)
        return (
            int(hex_value[0:2], 16),
            int(hex_value[2:4], 16),
            int(hex_value[4:6], 16),
        )

    @staticmethod
    def _rgb_tuple_to_hex(rgb):
        red, green, blue = rgb
        return "#{:02x}{:02x}{:02x}".format(
            max(0, min(255, int(red))),
            max(0, min(255, int(green))),
            max(0, min(255, int(blue))),
        )

    @staticmethod
    def _mix_color(base_hex, target_rgb, ratio):
        base_red, base_green, base_blue = TagBehavior._hex_to_rgb_tuple(base_hex)
        mixed = (
            (base_red * (1 - ratio)) + (target_rgb[0] * ratio),
            (base_green * (1 - ratio)) + (target_rgb[1] * ratio),
            (base_blue * (1 - ratio)) + (target_rgb[2] * ratio),
        )
        return TagBehavior._rgb_tuple_to_hex(mixed)

    @staticmethod
    def _hex_to_text_color(hex_color):
        hex_value = (hex_color or "").lstrip("#")
        if len(hex_value) != 6:
            return "#ffffff"
        red = int(hex_value[0:2], 16)
        green = int(hex_value[2:4], 16)
        blue = int(hex_value[4:6], 16)
        luminance = (0.299 * red) + (0.587 * green) + (0.114 * blue)
        return "#111827" if luminance >= 156 else "#f9fafb"

    @property
    def text_color(self):
        return self._hex_to_text_color(self.color)

    @staticmethod
    def _build_color_candidate(seed):
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        base_index = int(digest[:8], 16) % len(VIBRANT_TAG_COLORS)
        base_color = VIBRANT_TAG_COLORS[base_index]
        variant = int(digest[8:10], 16) % 7
        if variant == 0:
            return base_color
        if variant == 1:
            return TagBehavior._mix_color(base_color, (255, 255, 255), 0.12)
        if variant == 2:
            return TagBehavior._mix_color(base_color, (255, 255, 255), 0.22)
        if variant == 3:
            return TagBehavior._mix_color(base_color, (0, 0, 0), 0.12)
        if variant == 4:
            return TagBehavior._mix_color(base_color, (0, 0, 0), 0.22)
        if variant == 5:
            return TagBehavior._mix_color(base_color, (0, 0, 0), 0.32)
        return TagBehavior._mix_color(base_color, (255, 255, 255), 0.32)

    def _assign_unique_color(self):
        base_seed = f"{self.name}:{self.pk or 'new'}"
        for attempt in range(256):
            candidate = self._build_color_candidate(f"{base_seed}:{attempt}")
            queryset = type(self).objects.filter(color=candidate)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            if not queryset.exists():
                self.color = candidate
                return
        raise RuntimeError("タグ色の割り当てに失敗しました")

    def save(self, *args, **kwargs):
        if self.name:
            self.name = " ".join(self.name.strip().split())
        if not self.color:
            self._assign_unique_color()
        super().save(*args, **kwargs)


class ActivityLogBehavior:
    def _get_ordered_activity_items(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {})
        prefetched_items = prefetched.get("activitylogitem_set")
        if prefetched_items is not None:
            return list(prefetched_items)
        return list(self.activitylogitem_set.select_related("item").order_by("order"))

    def get_item_names(self):
        items = self._get_ordered_activity_items()
        if items:
            return ", ".join([item.item.name for item in items])
        return self.title or ""


class DomainFieldDefinitionBehavior:
    def clean(self):
        if self.key:
            self.key = self.key.strip().lower()
        if not re.fullmatch(r"[a-z][a-z0-9_]*", self.key or ""):
            raise ValidationError({"key": "半角英小文字で開始、英小文字/数字/_ のみで入力してください。"})
        if self.field_type in {self.TYPE_SELECT, self.TYPE_MULTISELECT}:
            if not isinstance(self.choices_json, list) or not all(
                isinstance(item, str) and item.strip() for item in self.choices_json
            ):
                raise ValidationError({"choices_json": "選択型では空でない文字列配列を指定してください。"})
        elif self.choices_json not in ([], None):
            raise ValidationError({"choices_json": "選択型以外では空配列 [] にしてください。"})


class VideoBehavior:
    @property
    def is_processing_pending(self):
        return self.processing_status == self.PROCESSING_PENDING

    @property
    def is_processing_running(self):
        return self.processing_status == self.PROCESSING_RUNNING

    @property
    def is_processing_ready(self):
        return self.processing_status == self.PROCESSING_READY

    @property
    def is_processing_failed(self):
        return self.processing_status == self.PROCESSING_FAILED

    def mark_processing_pending(self):
        if self.thumbnail and getattr(self.thumbnail, "_committed", False):
            self.thumbnail = None
        self.processing_status = self.PROCESSING_PENDING
        self.processing_step = "queued"
        self.processing_progress_percent = 0
        self.processing_error = ""
        self.processed_at = None

    def mark_processing_running(self):
        self.processing_status = self.PROCESSING_RUNNING
        if not self.processing_step:
            self.processing_step = "running"
        self.processing_error = ""

    def mark_processing_ready(self):
        self.processing_status = self.PROCESSING_READY
        self.processing_step = "ready"
        self.processing_progress_percent = 100
        self.processing_error = ""
        self.thumbnail_regeneration_requested = False
        self.processed_at = timezone.now()

    def mark_processing_failed(self, error_message):
        self.processing_status = self.PROCESSING_FAILED
        self.processing_step = "failed"
        self.processing_error = error_message
        self.thumbnail_regeneration_requested = False

    def prepare_thumbnail_regeneration(self):
        self.processing_status = self.PROCESSING_PENDING
        self.processing_step = "thumbnail"
        self.processing_progress_percent = 0
        self.processing_error = ""
        self.thumbnail_regeneration_requested = True
        self.processed_at = None

    def processing_step_display(self):
        labels = {
            "queued": "待機中",
            "running": "処理中",
            "transcoding": "圧縮中",
            "thumbnail": "サムネ生成中",
            "finalizing": "保存中",
            "ready": "完了",
            "failed": "失敗",
        }
        return labels.get(self.processing_step or "", "-")

    @property
    def is_portrait_video(self):
        width = int(self.video_width or 0)
        height = int(self.video_height or 0)
        return bool(width > 0 and height > width)

    @property
    def video_orientation_class(self):
        return "is-portrait" if self.is_portrait_video else "is-landscape"

    @property
    def watch_url(self):
        route_name = "piano_map:video_short_detail" if self.is_portrait_video else "piano_map:video_detail"
        return reverse(route_name, args=[self.id])

    @property
    def video_file_size_display(self):
        if not self.video_file:
            return "-"
        try:
            size = getattr(self.video_file, "size", None)
        except (FileNotFoundError, OSError, ValueError):
            return "-"
        if size is None:
            return "-"
        units = ["B", "KB", "MB", "GB"]
        value = float(size)
        unit = units[0]
        for next_unit in units:
            unit = next_unit
            if value < 1024 or next_unit == units[-1]:
                break
            value /= 1024
        return f"{value:.1f} {unit}"
