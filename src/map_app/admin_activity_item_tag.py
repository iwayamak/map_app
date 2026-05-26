from django.contrib import admin
from django.core.cache import cache
from django.shortcuts import redirect
from django.utils.html import format_html

from map_app.cache_keys import MAP_PAGE_CACHE_KEY
from map_app.domain_terms import get_domain_term_bool


def build_activity_item_admin(
    *,
    simple_delete_list_admin_mixin,
    site_settings_loader,
):
    class ActivityItemAdmin(simple_delete_list_admin_mixin, admin.ModelAdmin):
        list_display = ("name", "delete_button")
        list_display_links = ("name",)
        search_fields = ("name",)
        ordering = ("name",)
        readonly_fields = ("created_at",)
        delete_button_css_class = "admin-delete-x activity-item-delete-x"

        class Media:
            css = {
                "all": ("map_app/css/admin_simple_list_base.css?v=1",)
            }

        @staticmethod
        def _use_record_items_enabled():
            settings_obj = site_settings_loader()
            terms = settings_obj.get_domain_terms() if settings_obj else {}
            return get_domain_term_bool(terms, "use_record_items", default=True)

        def has_module_permission(self, request):
            if not self._use_record_items_enabled():
                return False
            return super().has_module_permission(request)

        def has_view_permission(self, request, obj=None):
            if not self._use_record_items_enabled():
                return False
            return super().has_view_permission(request, obj=obj)

        def get_model_perms(self, request):
            if not self._use_record_items_enabled():
                return {}
            return super().get_model_perms(request)

    return ActivityItemAdmin


def build_tag_admin(
    *,
    sortable_admin_mixin,
    simple_delete_list_admin_mixin,
):
    class TagAdmin(sortable_admin_mixin, simple_delete_list_admin_mixin, admin.ModelAdmin):
        list_display = ("name", "color_chip", "delete_button")
        list_display_links = ("name",)
        search_fields = ("name",)
        ordering = ("order",)
        readonly_fields = ("color_chip", "created_at")
        delete_confirmation_template = "admin/piano_map/tag/delete_confirmation.html"
        delete_button_css_class = "admin-delete-x tag-delete-x"

        class Media:
            css = {
                "all": (
                    "map_app/css/admin_simple_list_base.css?v=1",
                    "map_app/css/admin_tag_sortable.css?v=5",
                )
            }

        def __init__(self, model, admin_site):
            super().__init__(model, admin_site)
            # Rename reorder column label from "表示順" to a shorter "順".
            if hasattr(self, "_reorder_") and hasattr(self._reorder_, "__func__"):
                self._reorder_.__func__.short_description = "順"

        def get_changelist_instance(self, request):
            changelist = super().get_changelist_instance(request)
            self.enable_sorting = True
            self.order_by = "order"
            return changelist

        def changelist_view(self, request, extra_context=None):
            if "o" in request.GET:
                params = request.GET.copy()
                params.pop("o", None)
                query = params.urlencode()
                return redirect(f"{request.path}?{query}" if query else request.path)
            return super().changelist_view(request, extra_context=extra_context)

        def update_order(self, request):
            response = super().update_order(request)
            if response.status_code == 200:
                cache.delete(MAP_PAGE_CACHE_KEY)
            return response

        def color_chip(self, obj):
            return format_html(
                "<span style='display:inline-flex;align-items:center;border-radius:6px;padding:2px 8px;background:{};color:{};font-size:12px;font-weight:600;'>{}</span>",
                obj.color,
                obj.text_color,
                obj.color,
            )

        color_chip.short_description = "色"

    return TagAdmin
