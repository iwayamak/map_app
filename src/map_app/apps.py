from django.apps import AppConfig
from django.conf import settings


class MapAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "map_app"
    verbose_name = "マップアプリ"

    def ready(self):
        self.verbose_name = getattr(settings, "MAP_APP_ADMIN_APP_VERBOSE_NAME", "マップ")
        if not getattr(settings, "MAP_APP_DEFAULT_DOMAIN_TERMS_FUNC", ""):
            return
        if not getattr(settings, "MAP_APP_MAP_ASSETS_MODULE", ""):
            return

        from map_app.admin_site_context import install_admin_site_context
        from map_app.domain import get_default_domain_terms_func
        from map_app.models import ActivityItem, ActivityLog, Location, SiteSettings, Tag, Video
        from map_app.signals import connect_default_map_cache_invalidation

        install_admin_site_context(
            site_settings_model=SiteSettings,
            default_domain_terms_func=get_default_domain_terms_func(),
            location_model=Location,
            tag_model=Tag,
            activity_log_model=ActivityLog,
            activity_item_model=ActivityItem,
            video_model=Video,
            site_settings_verbose_default="サイト設定",
            app_title_default=getattr(settings, "MAP_APP_SITE_TITLE_DEFAULT", "マップ"),
        )
        connect_default_map_cache_invalidation()
