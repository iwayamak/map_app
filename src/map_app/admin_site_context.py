from django.conf import settings
from django.contrib import admin


def hide_shared_admin_app_entries(app_list, app_label=None):
    app_list = [app for app in app_list if app.get("app_label") != "map_app"]
    if app_label == "map_app":
        return []
    return app_list


def install_admin_site_context(
    *,
    site_settings_model,
    default_domain_terms_func,
    location_model,
    tag_model,
    activity_log_model,
    activity_item_model,
    video_model,
    site_settings_verbose_default="サイト設定",
    app_title_default="マップ",
):
    original_get_app_list = admin.site.get_app_list
    original_each_context = admin.site.each_context

    def _resolve_site_context():
        try:
            settings_obj = site_settings_model.load()
            if settings_obj:
                return settings_obj, settings_obj.get_domain_terms()
        except Exception:
            pass
        return None, default_domain_terms_func()

    def _apply_admin_labels(terms):
        app_title = (terms.get("app_title") or app_title_default).strip()
        admin.site.site_header = f"{app_title} 管理画面"
        admin.site.site_title = app_title
        admin.site.index_title = "ダッシュボード"

        location_model._meta.verbose_name = terms.get("admin_label_location", "場所")
        location_model._meta.verbose_name_plural = terms.get("admin_label_location", "場所")
        tag_model._meta.verbose_name = terms.get("admin_label_tag", "タグ")
        tag_model._meta.verbose_name_plural = terms.get("admin_label_tag", "タグ")
        activity_log_model._meta.verbose_name = terms.get("admin_label_activity_log", "記録")
        activity_log_model._meta.verbose_name_plural = terms.get("admin_label_activity_log", "記録")
        activity_item_model._meta.verbose_name = terms.get("admin_label_activity_item", "記録項目マスター")
        activity_item_model._meta.verbose_name_plural = terms.get("admin_label_activity_item", "記録項目マスター")
        video_model._meta.verbose_name = terms.get("admin_label_video", "動画")
        video_model._meta.verbose_name_plural = terms.get("admin_label_video", "動画")
        site_settings_model._meta.verbose_name = terms.get("admin_label_site_settings", site_settings_verbose_default)
        site_settings_model._meta.verbose_name_plural = terms.get("admin_label_site_settings", site_settings_verbose_default)

    def _patched_get_app_list(request, app_label=None):
        app_list = original_get_app_list(request, app_label=app_label)
        if getattr(settings, "MAP_APP_HIDE_SHARED_ADMIN_APP", False):
            app_list = hide_shared_admin_app_entries(app_list, app_label=app_label)
        terms = getattr(request, "_piano_map_domain_terms", None)
        if terms is None:
            _, terms = _resolve_site_context()
            request._piano_map_domain_terms = terms
        _apply_admin_labels(terms)

        model_label_map = {
            "Location": terms.get("admin_label_location", "場所"),
            "Tag": terms.get("admin_label_tag", "タグ"),
            "ActivityLog": terms.get("admin_label_activity_log", "記録"),
            "ActivityItem": terms.get("admin_label_activity_item", "記録項目マスター"),
            "Video": terms.get("admin_label_video", "動画"),
            "SiteSettings": terms.get("admin_label_site_settings", site_settings_verbose_default),
        }

        for app in app_list:
            if app.get("app_label") not in {"map_app", "piano_map"}:
                continue
            for model in app.get("models", []):
                object_name = model.get("object_name")
                if object_name in model_label_map and model_label_map[object_name]:
                    model["name"] = model_label_map[object_name]
        return app_list

    def _patched_each_context(request):
        context = original_each_context(request)
        terms = getattr(request, "_piano_map_domain_terms", None)
        if terms is None:
            settings_obj, terms = _resolve_site_context()
            request._piano_map_domain_terms = terms
            request._piano_map_site_settings = settings_obj
        else:
            settings_obj = getattr(request, "_piano_map_site_settings", None)
        _apply_admin_labels(terms)
        try:
            if settings_obj is None:
                settings_obj = site_settings_model.load()
            context["admin_site_logo_url"] = settings_obj.site_logo.url if settings_obj and settings_obj.site_logo else ""
        except Exception:
            context["admin_site_logo_url"] = ""
        context["admin_header_logo_emoji"] = (terms.get("header_logo_emoji") or "🎹").strip()
        context["admin_header_subtitle"] = (terms.get("subtitle") or "").strip()
        header_bg_mode = (terms.get("header_bg_mode") or "gradient").strip()
        if header_bg_mode == "solid":
            color = (terms.get("header_bg_solid_color") or "#667eea").strip()
            context["admin_header_style"] = f"background: {color} !important;"
        else:
            angle = terms.get("header_bg_gradient_angle", 135)
            try:
                angle = int(angle)
            except (TypeError, ValueError):
                angle = 135
            start = (terms.get("header_bg_gradient_from") or "#667eea").strip()
            end = (terms.get("header_bg_gradient_to") or "#764ba2").strip()
            context["admin_header_style"] = (
                f"background: linear-gradient({angle}deg, {start} 0%, {end} 100%) !important;"
            )
        return context

    admin.site.get_app_list = _patched_get_app_list
    admin.site.each_context = _patched_each_context
