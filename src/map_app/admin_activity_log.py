from datetime import datetime
import hashlib

from django import forms
from django.contrib import admin, messages
from django.core.cache import cache
from django.db.models import Count, Prefetch
from django.shortcuts import redirect, render
from django.urls import reverse

from map_app.domain_terms import get_domain_term_bool


def build_activity_log_admin(
    *,
    activity_log_model,
    activity_log_item_model,
    domain_field_definition_model,
    location_model,
    csv_admin_mixin,
    simple_delete_list_admin_mixin,
    build_csv_response,
    decode_uploaded_csv,
    build_dynamic_form_fields,
    extract_dynamic_cleaned_data,
    get_active_definitions,
    site_settings_loader,
    build_dynamic_form_field=None,
    include_dynamic_declared_fields=False,
    changelist_url_name="admin:piano_map_activitylog_changelist",
):
    if include_dynamic_declared_fields and build_dynamic_form_field is None:
        raise ValueError("build_dynamic_form_field is required when include_dynamic_declared_fields is enabled.")

    class ActivityLogAdminForm(forms.ModelForm):
        class Meta:
            model = activity_log_model
            fields = "__all__"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            definitions = get_active_definitions(domain_field_definition_model.TARGET_ACTIVITY_LOG)
            custom_data = self.instance.custom_data if self.instance and isinstance(self.instance.custom_data, dict) else {}
            self.dynamic_field_names = build_dynamic_form_fields(self, definitions, custom_data)
            self.dynamic_definitions = definitions

        def clean(self):
            cleaned = super().clean()
            cleaned["custom_data"] = extract_dynamic_cleaned_data(cleaned, getattr(self, "dynamic_definitions", []))
            return cleaned

        def save(self, commit=True):
            instance = super().save(commit=False)
            instance.custom_data = self.cleaned_data.get("custom_data", {})
            if commit:
                instance.save()
                self.save_m2m()
            return instance

    class ActivityLogItemInline(admin.TabularInline):
        model = activity_log_item_model
        extra = 1
        min_num = 0
        autocomplete_fields = ["item"]
        fields = ("item",)
        ordering = ("order",)
        verbose_name = "記録項目"
        verbose_name_plural = "記録項目"

        class Media:
            css = {
                "all": ("piano_map/css/admin_order_display.css?v=30",)
            }
            js = (
                "admin/js/jquery.init.js",
                "admin/js/inlines.js",
                "piano_map/js/admin_date_fix.js?v=2",
                "piano_map/js/admin_inline_fix.js?v=5",
            )

    class ActivityLogAdmin(csv_admin_mixin, simple_delete_list_admin_mixin, admin.ModelAdmin):
        form = ActivityLogAdminForm
        list_display = ("date", "location", "activity_item_count", "delete_button")
        list_display_links = ("date",)
        list_filter = ("date", "location", "created_at")
        search_fields = ("title", "location__name", "activitylogitem__item__name")
        date_hierarchy = "date"
        autocomplete_fields = ["location"]
        inlines = [ActivityLogItemInline]
        csv_import_url_name = "activitylog_import_csv"
        csv_export_url_name = "activitylog_export_all_csv"
        delete_button_css_class = "admin-delete-x performance-delete-x"

        class Media:
            css = {
                "all": (
                    "piano_map/css/admin_calendar.css?v=1",
                    "piano_map/css/admin_mobile.css?v=18",
                    "piano_map/css/admin_simple_list_base.css?v=1",
                    "piano_map/css/admin_performance_simple_list.css?v=4",
                )
            }

        @staticmethod
        def _use_record_items_enabled():
            settings_obj = site_settings_loader()
            terms = settings_obj.get_domain_terms() if settings_obj else {}
            return get_domain_term_bool(terms, "use_record_items", default=True)

        def get_inline_instances(self, request, obj=None):
            if not self._use_record_items_enabled():
                return []
            return super().get_inline_instances(request, obj=obj)

        def get_search_fields(self, request):
            fields = list(super().get_search_fields(request))
            if not self._use_record_items_enabled():
                fields = [field for field in fields if field != "activitylogitem__item__name"]
            return tuple(fields)

        def get_list_display(self, request):
            fields = list(super().get_list_display(request))
            if not self._use_record_items_enabled():
                fields = [field for field in fields if field != "activity_item_count"]
            return tuple(fields)

        def activity_item_count(self, obj):
            count = getattr(obj, "activity_item_count_value", None)
            if count is None:
                count = obj.activitylogitem_set.count()
            return f"{count}件"

        activity_item_count.short_description = "項目数"
        activity_item_count.admin_order_field = "activity_item_count_value"

        fieldsets = (
            ("基本情報", {
                "fields": ("location", "date")
            }),
        )

        def get_fieldsets(self, request, obj=None):
            base_fieldsets = list(super().get_fieldsets(request, obj))
            definitions = get_active_definitions(domain_field_definition_model.TARGET_ACTIVITY_LOG)
            dynamic_field_names = [f"dyn__{definition.key}" for definition in definitions]
            if dynamic_field_names:
                base_fieldsets.append(
                    (
                        "追加項目",
                        {
                            "fields": tuple(dynamic_field_names),
                            "classes": ("wide",),
                            "description": "ドメイン項目定義に基づく追加入力項目です。",
                        },
                    )
                )
            return tuple(base_fieldsets)

        if include_dynamic_declared_fields:
            def get_form(self, request, obj=None, change=False, **kwargs):
                definitions = get_active_definitions(domain_field_definition_model.TARGET_ACTIVITY_LOG)
                dynamic_declared_fields = {}
                for definition in definitions:
                    field = build_dynamic_form_field(definition)
                    if field is None:
                        continue
                    dynamic_declared_fields[f"dyn__{definition.key}"] = field
                if dynamic_declared_fields:
                    kwargs["form"] = type("ActivityLogAdminDynamicForm", (self.form,), dynamic_declared_fields)
                return super().get_form(request, obj, change, **kwargs)

        def get_queryset(self, request):
            queryset = super().get_queryset(request)
            return queryset.select_related("location").annotate(activity_item_count_value=Count("activitylogitem"))

        def get_delete_button_label(self, obj):
            return f"{obj.location.name} ({obj.date})"

        def save_related(self, request, form, formsets, change):
            super().save_related(request, form, formsets, change)

            instance = form.instance
            activity_log_items = activity_log_item_model.objects.filter(activity_log=instance).order_by("id")

            for index, activity_log_item in enumerate(activity_log_items):
                activity_log_item.order = index
                activity_log_item.save(update_fields=["order"])

        def _build_submit_guard_key(self, request):
            payload_parts = []
            for key in sorted(request.POST.keys()):
                if key == "csrfmiddlewaretoken":
                    continue
                for value in request.POST.getlist(key):
                    payload_parts.append(f"{key}={value}")
            payload = "&".join(payload_parts)
            digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            return f"piano_map:admin:activitylog:submit_guard:{request.user.pk}:{digest}"

        def _is_duplicate_add_submit(self, request):
            key = self._build_submit_guard_key(request)
            timeout = 10
            return not cache.add(key, "1", timeout=timeout)

        def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
            is_add = object_id is None
            if is_add and request.method == "POST" and self._is_duplicate_add_submit(request):
                messages.warning(request, "同じ内容の送信が短時間で検出されたため、重複登録を防止しました。")
                return redirect(reverse(changelist_url_name))
            return super().changeform_view(request, object_id, form_url, extra_context)

        def export_as_csv(self, request, queryset):
            queryset = queryset.select_related("location").prefetch_related(
                Prefetch(
                    "activitylogitem_set",
                    queryset=activity_log_item_model.objects.select_related("item").order_by("order"),
                )
            )

            row_data = []
            max_activity_item_count = 1
            for obj in queryset:
                item_names = [activity_log_item.item.name for activity_log_item in obj._get_ordered_activity_items()]
                if not item_names and obj.title:
                    item_names = [name.strip() for name in obj.title.split(",") if name.strip()]
                max_activity_item_count = max(max_activity_item_count, len(item_names))
                row_data.append((obj.location.name, obj.date.strftime("%Y-%m-%d"), item_names))

            header = ["場所名", "記録日"] + [f"項目名{i}" for i in range(1, max_activity_item_count + 1)]
            rows = [
                [location_name, date_text, *item_names, *([""] * (max_activity_item_count - len(item_names)))]
                for location_name, date_text, item_names in row_data
            ]
            return build_csv_response("performances", header, rows)

        export_as_csv.short_description = "選択した記録をCSVエクスポート"

        def import_csv(self, request):
            if request.method == "POST":
                try:
                    reader = decode_uploaded_csv(request.FILES.get("csv_file"))
                    created_count = 0
                    error_rows = []

                    for idx, row in enumerate(reader, start=2):
                        try:
                            location = location_model.objects.get(name=row["場所名"])
                            date_text = row.get("記録日") or row.get("演奏日") or ""
                            date_obj = datetime.strptime(date_text, "%Y-%m-%d").date()

                            activity_log_model.objects.create(
                                location=location,
                                date=date_obj,
                                title=row.get("項目名") or row.get("曲名") or "",
                            )
                            created_count += 1
                        except location_model.DoesNotExist:
                            error_rows.append(f'行{idx}: 場所「{row["場所名"]}」が見つかりません')
                        except (KeyError, TypeError, ValueError) as exc:
                            error_rows.append(f"行{idx}: {str(exc)}")

                    if error_rows:
                        messages.warning(request, f"{created_count}件作成しました。エラー: " + ", ".join(error_rows[:5]))
                    else:
                        messages.success(request, f"インポート完了: {created_count}件作成")
                except ValueError as exc:
                    messages.error(request, str(exc))
                except (KeyError, TypeError) as exc:
                    messages.error(request, f"CSV列の形式が不正です: {str(exc)}")

                return redirect("..")

            return render(request, "admin/csv_import.html")

    return ActivityLogAdmin
