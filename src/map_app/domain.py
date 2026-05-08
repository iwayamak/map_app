from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


def _required_setting(name):
    value = getattr(settings, name, None)
    if not isinstance(value, str) or not value.strip():
        raise ImproperlyConfigured(f"{name} must be set for map_app domain binding.")
    return value.strip()


def template_name(key, default):
    value = getattr(settings, key, default)
    value = str(value).strip()
    if not value:
        raise ImproperlyConfigured(f"{key} must be set for map_app template binding.")
    return value


@lru_cache(maxsize=1)
def get_site_settings_model():
    return import_string(_required_setting("MAP_APP_SITE_SETTINGS_MODEL"))


@lru_cache(maxsize=1)
def get_tag_model():
    return import_string(_required_setting("MAP_APP_TAG_MODEL"))


@lru_cache(maxsize=1)
def get_location_model():
    return import_string(_required_setting("MAP_APP_LOCATION_MODEL"))


@lru_cache(maxsize=1)
def get_activity_log_model():
    return import_string(_required_setting("MAP_APP_ACTIVITY_LOG_MODEL"))


@lru_cache(maxsize=1)
def get_activity_log_item_model():
    return import_string(_required_setting("MAP_APP_ACTIVITY_LOG_ITEM_MODEL"))


@lru_cache(maxsize=1)
def get_location_photo_model():
    return import_string(_required_setting("MAP_APP_LOCATION_PHOTO_MODEL"))


@lru_cache(maxsize=1)
def get_domain_field_definition_model():
    return import_string(_required_setting("MAP_APP_DOMAIN_FIELD_DEFINITION_MODEL"))


@lru_cache(maxsize=1)
def get_video_model():
    return import_string(_required_setting("MAP_APP_VIDEO_MODEL"))


@lru_cache(maxsize=1)
def get_default_domain_terms_func():
    return import_string(_required_setting("MAP_APP_DEFAULT_DOMAIN_TERMS_FUNC"))


@lru_cache(maxsize=1)
def get_statistics_builder():
    return import_string(_required_setting("MAP_APP_BUILD_MAP_STATISTICS_FUNC"))


@lru_cache(maxsize=1)
def _get_map_assets_module():
    module_path = _required_setting("MAP_APP_MAP_ASSETS_MODULE")
    return __import__(module_path, fromlist=["*"])


def map_css_link_tags():
    return _get_map_assets_module().map_css_link_tags()


def map_js_script_tags():
    return _get_map_assets_module().map_js_script_tags()


def map_cache_key(suffix):
    return _get_map_assets_module().map_cache_key(suffix)
