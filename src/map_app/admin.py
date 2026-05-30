from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin

from map_app.admin_activity_item_tag import build_activity_item_admin, build_tag_admin
from map_app.admin_activity_log import build_activity_log_admin
from map_app.admin_common import CsvAdminMixin, SimpleDeleteListAdminMixin, build_csv_response, decode_uploaded_csv
from map_app.admin_domain_fields import (
    build_dynamic_form_fields,
    extract_dynamic_cleaned_data,
    get_active_definitions as _get_active_definitions,
)
from map_app.admin_location import build_location_admin
from map_app.admin_sitesettings import build_sitesettings_admin
from map_app.models import (
    ActivityItem,
    ActivityLog,
    ActivityLogItem,
    DomainFieldDefinition,
    Location,
    LocationPhoto,
    SiteSettings,
    Tag,
)
from map_app.services.location_duplicate_service import detect_location_duplicates, merge_locations

from .admin_domain_field import DomainFieldDefinitionAdmin
from .admin_video import VideoAdmin
from .domain import get_default_domain_terms_func
from .models import Video


def get_active_definitions(target):
    return _get_active_definitions(DomainFieldDefinition, target)


@admin.register(Location)
class LocationAdmin(
    build_location_admin(
        location_model=Location,
        location_photo_model=LocationPhoto,
        tag_model=Tag,
        domain_field_definition_model=DomainFieldDefinition,
        csv_admin_mixin=CsvAdminMixin,
        simple_delete_list_admin_mixin=SimpleDeleteListAdminMixin,
        build_csv_response=build_csv_response,
        decode_uploaded_csv=decode_uploaded_csv,
        extract_dynamic_cleaned_data=extract_dynamic_cleaned_data,
        get_active_definitions=get_active_definitions,
        build_dynamic_form_fields=build_dynamic_form_fields,
        detect_location_duplicates=detect_location_duplicates,
        merge_locations=merge_locations,
        use_prefetched_tags=True,
        include_dynamic_declared_fields=False,
    )
):
    pass


@admin.register(ActivityLog)
class ActivityLogAdmin(
    build_activity_log_admin(
        activity_log_model=ActivityLog,
        activity_log_item_model=ActivityLogItem,
        domain_field_definition_model=DomainFieldDefinition,
        location_model=Location,
        csv_admin_mixin=CsvAdminMixin,
        simple_delete_list_admin_mixin=SimpleDeleteListAdminMixin,
        build_csv_response=build_csv_response,
        decode_uploaded_csv=decode_uploaded_csv,
        build_dynamic_form_fields=build_dynamic_form_fields,
        extract_dynamic_cleaned_data=extract_dynamic_cleaned_data,
        get_active_definitions=get_active_definitions,
        site_settings_loader=SiteSettings.load_cached,
        changelist_url_name="admin:map_app_activitylog_changelist",
    )
):
    pass


@admin.register(ActivityItem)
class ActivityItemAdmin(
    build_activity_item_admin(
        simple_delete_list_admin_mixin=SimpleDeleteListAdminMixin,
        site_settings_loader=SiteSettings.load_cached,
    )
):
    pass


@admin.register(Tag)
class TagAdmin(
    build_tag_admin(
        sortable_admin_mixin=SortableAdminMixin,
        simple_delete_list_admin_mixin=SimpleDeleteListAdminMixin,
    )
):
    pass


@admin.register(SiteSettings)
class SiteSettingsAdmin(
    build_sitesettings_admin(SiteSettings, get_default_domain_terms_func()), admin.ModelAdmin
):
    pass


admin.site.register(DomainFieldDefinition, DomainFieldDefinitionAdmin)
admin.site.register(Video, VideoAdmin)
