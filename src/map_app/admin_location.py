from django import forms
from django.contrib import admin, messages
from django.db.models import Count, Prefetch
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join


PLAYABLE_SCHEDULE_NOTE_MAX_LENGTH = 40


def build_location_admin(
    *,
    location_model,
    location_photo_model,
    tag_model,
    domain_field_definition_model,
    csv_admin_mixin,
    simple_delete_list_admin_mixin,
    build_csv_response,
    decode_uploaded_csv,
    extract_dynamic_cleaned_data,
    get_active_definitions,
    build_dynamic_form_fields,
    detect_location_duplicates,
    merge_locations,
    build_dynamic_form_field=None,
    use_prefetched_tags=False,
    include_dynamic_declared_fields=False,
):
    class LocationPhotoInline(admin.TabularInline):
        model = location_photo_model

        class LocationPhotoInlineForm(forms.ModelForm):
            class Meta:
                model = location_photo_model
                fields = "__all__"
                help_texts = {
                    "image": "推奨: 1枚あたり5MB以下、長辺2560px以下。1つの場所につき20枚程度までを目安にしてください。",
                }

        form = LocationPhotoInlineForm
        extra = 1
        min_num = 0
        fields = ("image",)
        ordering = ("order", "id")
        verbose_name = "場所写真"
        verbose_name_plural = "場所写真"

    class LocationTagInline(admin.TabularInline):
        model = location_model.tags.through
        extra = 1
        min_num = 0
        autocomplete_fields = ["tag"]
        verbose_name = "タグ"
        verbose_name_plural = "タグ"

    class LocationAdminForm(forms.ModelForm):
        class Meta:
            model = location_model
            fields = "__all__"
            widgets = {
                "playable_schedule_note": forms.Textarea(
                    attrs={
                        "rows": 3,
                        "maxlength": PLAYABLE_SCHEDULE_NOTE_MAX_LENGTH,
                    }
                ),
                "detail_note": forms.Textarea(
                    attrs={
                        "rows": 6,
                        "placeholder": "モーダルに表示したい補足情報を自由入力で記載できます。改行も保持されます。",
                    }
                ),
            }
            help_texts = {
                "playable_schedule_note": f"最大{PLAYABLE_SCHEDULE_NOTE_MAX_LENGTH}文字。ヘッダ要約で表示されます。",
                "detail_note": "詳細モーダルの本文として表示されます。長文や補足説明はこちらに入力してください。",
            }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            definitions = get_active_definitions(domain_field_definition_model.TARGET_LOCATION)
            custom_data = self.instance.custom_data if self.instance and isinstance(self.instance.custom_data, dict) else {}
            self.dynamic_field_names = build_dynamic_form_fields(self, definitions, custom_data)
            self.dynamic_definitions = definitions

        def clean_playable_schedule_note(self):
            value = (self.cleaned_data.get("playable_schedule_note") or "").strip()
            if len(value) > PLAYABLE_SCHEDULE_NOTE_MAX_LENGTH:
                raise forms.ValidationError(
                    f"利用案内は{PLAYABLE_SCHEDULE_NOTE_MAX_LENGTH}文字以内で入力してください。"
                )
            return value

        def clean_detail_note(self):
            return (self.cleaned_data.get("detail_note") or "").strip()

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

    class LocationAdmin(csv_admin_mixin, simple_delete_list_admin_mixin, admin.ModelAdmin):
        form = LocationAdminForm
        exclude = ("tags",)
        list_display = ("name", "get_tags_display", "delete_button")
        list_display_links = ("name",)
        search_fields = ("name", "tags__name")
        list_filter = ("name", "tags")
        inlines = [LocationPhotoInline, LocationTagInline]
        csv_import_url_name = "location_import_csv"
        csv_export_url_name = "location_export_all_csv"
        delete_confirmation_template = "admin/piano_map/location/delete_confirmation.html"
        delete_button_css_class = "admin-delete-x location-delete-x"

        class Media:
            css = {
                "all": (
                    "piano_map/css/admin_mobile.css?v=18",
                    "piano_map/css/admin_location_photo.css?v=17",
                    "piano_map/css/admin_location_tag.css?v=4",
                    "piano_map/css/admin_simple_list_base.css?v=1",
                    "piano_map/css/admin_location_simple_list.css?v=2",
                )
            }
            js = (
                "piano_map/js/admin_geocoding.js?v=20",
                "piano_map/js/admin_location_simple_list.js?v=1",
            )

        fieldsets = (
            ("場所情報", {"fields": ("name",), "classes": ("wide",)}),
            ("位置情報", {"fields": ("latitude", "longitude"), "classes": ("wide",)}),
            (
                "案内情報",
                {
                    "fields": ("nearest_station", "walking_minutes", "playable_schedule_note", "detail_note"),
                    "classes": ("wide",),
                    "description": "アクセス要約はヘッダ、詳細メモは本文セクションに表示されます。",
                },
            ),
        )

        def get_fieldsets(self, request, obj=None):
            base_fieldsets = list(super().get_fieldsets(request, obj))
            definitions = get_active_definitions(domain_field_definition_model.TARGET_LOCATION)
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
                definitions = get_active_definitions(domain_field_definition_model.TARGET_LOCATION)
                dynamic_declared_fields = {}
                for definition in definitions:
                    field = build_dynamic_form_field(definition)
                    if field is None:
                        continue
                    dynamic_declared_fields[f"dyn__{definition.key}"] = field
                if dynamic_declared_fields:
                    kwargs["form"] = type("LocationAdminDynamicForm", (self.form,), dynamic_declared_fields)
                return super().get_form(request, obj, change, **kwargs)

        def get_queryset(self, request):
            queryset = super().get_queryset(request)
            return queryset.prefetch_related("photos", "tags")

        def get_simple_list_tools(self, request):
            tools = [{"url": reverse("admin:location_duplicates"), "label": "重複候補を確認", "css_class": "historylink"}]
            tools.extend(super().get_simple_list_tools(request))
            return tools

        def get_urls(self):
            custom_urls = [
                path("duplicates/", self.admin_site.admin_view(self.duplicate_candidates_view), name="location_duplicates"),
                path("duplicates/merge/", self.admin_site.admin_view(self.merge_duplicate_view), name="location_duplicates_merge"),
            ]
            return custom_urls + super().get_urls()

        def get_tags_display(self, obj):
            if use_prefetched_tags:
                prefetched = getattr(obj, "_prefetched_objects_cache", {})
                prefetched_tags = prefetched.get("tags")
                if prefetched_tags is not None:
                    tags = sorted(
                        prefetched_tags,
                        key=lambda tag: (getattr(tag, "order", 0), getattr(tag, "name", "")),
                    )
                else:
                    tags = list(obj.tags.order_by("order", "name").only("name", "color"))
            else:
                tags = list(obj.tags.order_by("order", "name").only("name", "color"))
            if not tags:
                return "-"

            max_visible = 3
            visible_tags = tags[:max_visible]
            hidden_count = max(0, len(tags) - max_visible)
            all_tag_names = ", ".join(tag.name for tag in tags)
            chips_html = format_html_join(
                "",
                "<span style='display:inline-flex;align-items:center;border-radius:6px;padding:2px 8px;margin:0 6px 0 0;background:{};color:{};font-size:12px;font-weight:600;white-space:nowrap;'>{}</span>",
                ((tag.color, tag.text_color, tag.name) for tag in visible_tags),
            )
            if hidden_count > 0:
                chips_html += format_html(
                    "<span style='display:inline-flex;align-items:center;border-radius:999px;padding:2px 8px;margin:0 6px 0 0;background:#e5e7eb;color:#374151;font-size:11px;font-weight:700;'>+{}</span>",
                    hidden_count,
                )
            return format_html(
                "<span title='{}' style='display:flex;align-items:center;flex-wrap:wrap;gap:6px;white-space:normal;max-width:100%;'>{}</span>",
                all_tag_names,
                chips_html,
            )

        get_tags_display.short_description = "タグ"

        def export_as_csv(self, request, queryset):
            rows = ([obj.name, obj.latitude, obj.longitude, obj.image.name if obj.image else ""] for obj in queryset)
            return build_csv_response("locations", ["場所名", "緯度", "経度", "画像パス"], rows)

        export_as_csv.short_description = "選択した場所をCSVエクスポート"

        def import_csv(self, request):
            if request.method == "POST":
                try:
                    reader = decode_uploaded_csv(request.FILES.get("csv_file"))
                    created_count = 0
                    updated_count = 0
                    for row in reader:
                        _location, created = location_model.objects.update_or_create(
                            name=row["場所名"],
                            defaults={"latitude": float(row["緯度"]), "longitude": float(row["経度"])},
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                    messages.success(request, f"インポート完了: {created_count}件作成, {updated_count}件更新")
                except ValueError as exc:
                    messages.error(request, str(exc))
                except (KeyError, TypeError) as exc:
                    messages.error(request, f"CSV列の形式が不正です: {exc}")
                return redirect("..")
            return render(request, "admin/csv_import.html")

        def save_related(self, request, form, formsets, change):
            super().save_related(request, form, formsets, change)
            instance = form.instance
            location_photos = location_photo_model.objects.filter(location=instance).order_by("id")
            for index, photo in enumerate(location_photos):
                if photo.order != index:
                    photo.order = index
                    photo.save(update_fields=["order"])

        def duplicate_candidates_view(self, request):
            locations = (
                location_model.objects.all()
                .annotate(
                    activity_log_count=Count("activity_logs", distinct=True),
                    photo_count=Count("photos", distinct=True),
                )
                .prefetch_related(Prefetch("tags", queryset=tag_model.objects.only("id", "name").order_by("order", "name")))
            )
            candidates = detect_location_duplicates(locations)
            context = {
                **self.admin_site.each_context(request),
                "opts": self.model._meta,
                "title": "重複候補の確認",
                "candidates": candidates,
            }
            return render(request, "admin/location_duplicates.html", context)

        def merge_duplicate_view(self, request):
            if request.method != "POST":
                return redirect("admin:location_duplicates")
            try:
                primary_id = int(request.POST.get("primary_id", ""))
                duplicate_id = int(request.POST.get("duplicate_id", ""))
                merge_locations(primary_id=primary_id, duplicate_id=duplicate_id)
                messages.success(request, "場所を統合しました。")
            except ValueError as exc:
                messages.error(request, str(exc))
            except location_model.DoesNotExist:
                messages.error(request, "統合対象の場所が見つかりません。")
            return redirect("admin:location_duplicates")

    return LocationAdmin
