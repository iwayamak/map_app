import hashlib
import json
import uuid
from pathlib import Path

from django.contrib import admin, messages
from django import forms
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.conf import settings

from .models import Video
from .services.video_transcode_service import schedule_video_processing
from .validators import validate_video_file


class _DirectUploadedVideoFile:
    def __init__(self, *, name, size, content_type):
        self.name = name
        self.size = size
        self.content_type = content_type


class VideoAdminForm(forms.ModelForm):
    direct_upload_key = forms.CharField(required=False, widget=forms.HiddenInput())
    direct_upload_original_name = forms.CharField(required=False, widget=forms.HiddenInput())
    direct_upload_size = forms.IntegerField(required=False, min_value=1, widget=forms.HiddenInput())
    direct_upload_content_type = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Video
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["video_file"].required = False

    def clean(self):
        cleaned_data = super().clean()
        uploaded_file = cleaned_data.get("video_file")
        newly_uploaded_file = self.files.get(self.add_prefix("video_file")) or self.files.get("video_file")
        direct_upload_key = (cleaned_data.get("direct_upload_key") or "").strip()
        direct_upload_name = (cleaned_data.get("direct_upload_original_name") or "").strip()
        direct_upload_size = cleaned_data.get("direct_upload_size")
        direct_upload_content_type = (cleaned_data.get("direct_upload_content_type") or "").strip()

        if newly_uploaded_file and direct_upload_key:
            self.add_error("video_file", "通常アップロードと S3 直アップロードは同時に使えません。")
            return cleaned_data

        if direct_upload_key:
            relative_key = normalize_direct_upload_key(direct_upload_key)
            if not relative_key:
                self.add_error("video_file", "S3 直アップロードのキーが不正です。")
                return cleaned_data

            candidate = _DirectUploadedVideoFile(
                name=direct_upload_name or Path(relative_key).name,
                size=direct_upload_size or 0,
                content_type=direct_upload_content_type,
            )
            try:
                validate_video_file(candidate)
            except ValidationError as exc:
                self.add_error("video_file", exc)
                return cleaned_data

            cleaned_data["direct_upload_key"] = relative_key

        has_existing_file = bool(getattr(self.instance, "video_file", None))
        if not uploaded_file and not direct_upload_key and not has_existing_file:
            self.add_error("video_file", "動画ファイルを選択してください。")

        return cleaned_data

    def _post_clean(self):
        direct_upload_key = (self.cleaned_data.get("direct_upload_key") or "").strip() if hasattr(self, "cleaned_data") else ""
        if direct_upload_key and not self.cleaned_data.get("video_file"):
            self.instance.video_file.name = direct_upload_key
            self.instance._force_video_processing = True
        super()._post_clean()

    def save(self, commit=True):
        instance = super().save(commit=False)
        direct_upload_key = self.cleaned_data.get("direct_upload_key")
        if direct_upload_key:
            instance.video_file.name = direct_upload_key
            instance._force_video_processing = True
        if commit:
            instance.save()
            self.save_m2m()
        return instance


def build_direct_upload_key(filename):
    extension = Path(filename or "").suffix.lower()
    generated_name = f"videos/direct/{uuid.uuid4().hex}{extension}"
    media_location = (getattr(settings, "AWS_MEDIA_LOCATION", "") or "").strip().strip("/")
    if media_location:
        return f"{media_location}/{generated_name}", generated_name
    return generated_name, generated_name


def normalize_direct_upload_key(raw_key):
    value = (raw_key or "").strip().lstrip("/")
    if not value:
        return ""
    media_location = (getattr(settings, "AWS_MEDIA_LOCATION", "") or "").strip().strip("/")
    if media_location and value.startswith(f"{media_location}/"):
        return value[len(media_location) + 1:]
    return value


def build_s3_client():
    import boto3
    from botocore.config import Config

    client_kwargs = {
        "region_name": getattr(settings, "AWS_S3_REGION_NAME", None),
        "aws_access_key_id": getattr(settings, "AWS_ACCESS_KEY_ID", None),
        "aws_secret_access_key": getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
        "config": Config(signature_version="s3v4"),
    }
    endpoint_url = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url
    return boto3.client("s3", **client_kwargs)


class VideoAdmin(admin.ModelAdmin):
    form = VideoAdminForm
    change_list_template = "admin/map_app/video/change_list.html"
    change_form_template = "admin/map_app/video/change_form.html"
    actions = None
    list_display = (
        "title",
        "processing_status_badge",
        "processing_progress_live",
        "is_published",
        "is_featured",
        "featured_order",
        "published_at",
        "updated_at",
    )
    list_filter = ("processing_status", "is_published", "is_featured", "published_at", "created_at")
    search_fields = ("title", "description")
    ordering = ("-is_featured", "featured_order", "-published_at", "-created_at")
    readonly_fields = (
        "processing_status_readonly",
        "processing_step_readonly",
        "processing_progress_readonly",
        "processing_error_readonly",
        "processed_at",
        "video_file_size",
        "created_at",
        "updated_at",
    )

    class Media:
        css = {
            "all": (
                "map_app/css/admin_mobile.css?v=18",
                "map_app/css/admin_video_upload.css?v=1",
                "map_app/css/admin_video_list.css?v=1",
            )
        }
        js = (
            "map_app/js/admin_video_upload.js?v=2",
            "map_app/js/admin_video_processing_status.js?v=1",
        )

    fieldsets = (
        ("基本情報", {"fields": ("title", "description", "video_file", "video_file_size", "thumbnail")}),
        ("公開設定", {"fields": ("is_published", "published_at", "is_featured", "featured_order")}),
        ("処理状態", {"fields": ("processing_status_readonly", "processing_step_readonly", "processing_progress_readonly", "processing_error_readonly", "processed_at")}),
        ("システム情報", {"fields": ("created_at", "updated_at")}),
    )

    STANDARD_REDIRECT_BUTTONS = {"_continue", "_addanother"}

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "status/",
                self.admin_site.admin_view(self.status_view),
                name="map_app_video_status",
            ),
            path(
                "direct-upload-url/",
                self.admin_site.admin_view(self.direct_upload_url_view),
                name="map_app_video_direct_upload",
            ),
        ]
        return custom_urls + urls

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "video_file" and formfield is not None:
            formfield.widget.attrs["data-direct-upload-url"] = reverse("admin:map_app_video_direct_upload")
            formfield.widget.attrs["data-direct-upload-enabled"] = "1" if settings.USE_S3 else "0"
        return formfield

    def video_file_size(self, obj):
        if not obj or not obj.video_file:
            return "-"

        try:
            size = getattr(obj.video_file, "size", None)
        except (FileNotFoundError, OSError, ValueError):
            return "-"
        if size is None:
            return "-"

        return format_html("{} {}", f"{self._format_file_size(size):.1f}", self._resolve_file_size_unit(size))

    video_file_size.short_description = "現在の動画サイズ"

    @staticmethod
    def processing_progress(obj):
        if not obj:
            return "-"
        return f"{int(getattr(obj, 'processing_progress_percent', 0) or 0)}% / {obj.processing_step_display()}"

    processing_progress.short_description = "進捗"

    @admin.display(description="処理状態", ordering="processing_status")
    def processing_status_badge(self, obj):
        if not obj:
            return "-"
        return format_html(
            '<span class="video-admin-chip video-admin-chip-status video-admin-chip-status-{}" '
            'data-video-status-label="{}" data-video-status="{}">{}</span>',
            obj.processing_status,
            obj.pk,
            obj.processing_status,
            obj.get_processing_status_display(),
        )

    @admin.display(description="処理進捗", ordering="processing_progress_percent")
    def processing_progress_live(self, obj):
        if not obj:
            return "-"
        return format_html(
            '<div class="video-admin-progress" data-video-progress-root="{}">'
            '<div class="video-admin-progress-bar"><span class="video-admin-progress-fill" '
            'data-video-progress-bar="{}" style="width: {}%;"></span></div>'
            '<span class="video-admin-progress-text" data-video-progress-text="{}">{}% / {}</span>'
            '</div>',
            obj.pk,
            obj.pk,
            int(getattr(obj, "processing_progress_percent", 0) or 0),
            obj.pk,
            int(getattr(obj, "processing_progress_percent", 0) or 0),
            obj.processing_step_display(),
        )

    @admin.display(description="処理状態")
    def processing_status_readonly(self, obj):
        if not obj:
            return "-"
        return format_html(
            '<span data-video-status-label="{}" data-video-status="{}">{}</span>',
            obj.pk,
            obj.processing_status,
            obj.get_processing_status_display(),
        )

    @admin.display(description="処理段階")
    def processing_step_readonly(self, obj):
        if not obj:
            return "-"
        return format_html(
            '<span data-video-step-text="{}">{}</span>',
            obj.pk,
            obj.processing_step_display(),
        )

    @admin.display(description="進捗率")
    def processing_progress_readonly(self, obj):
        if not obj:
            return "-"
        return format_html(
            '<div class="video-admin-progress" data-video-progress-root="{}">'
            '<div class="video-admin-progress-bar"><span class="video-admin-progress-fill" '
            'data-video-progress-bar="{}" style="width: {}%;"></span></div>'
            '<span class="video-admin-progress-text" data-video-progress-percent="{}">{}%</span>'
            '</div>',
            obj.pk,
            obj.pk,
            int(getattr(obj, "processing_progress_percent", 0) or 0),
            obj.pk,
            int(getattr(obj, "processing_progress_percent", 0) or 0),
        )

    @admin.display(description="処理エラー")
    def processing_error_readonly(self, obj):
        if not obj:
            return "-"
        return format_html(
            '<div data-video-error-text="{}">{}</div>',
            obj.pk,
            obj.processing_error or "-",
        )

    @staticmethod
    def _format_file_size(size):
        value = float(size)
        for _ in ["B", "KB", "MB", "GB"]:
            if value < 1024:
                return value
            value /= 1024
        return value

    @staticmethod
    def _resolve_file_size_unit(size):
        value = float(size)
        units = ["B", "KB", "MB", "GB"]
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return unit
            value /= 1024
        return units[-1]

    def _uses_standard_redirect(self, request):
        return any(button_name in request.POST for button_name in self.STANDARD_REDIRECT_BUTTONS)

    @staticmethod
    def _get_add_success_message():
        return "✔ アップロードを受け付けました。圧縮とサムネイル生成をバックグラウンドで実行中です。"

    @staticmethod
    def _get_default_change_success_message():
        return "✔ 保存が完了しました。"

    @staticmethod
    def _get_processing_change_success_message():
        return "✔ 保存を受け付けました。必要な動画処理をバックグラウンドで実行中です。"

    def _get_change_success_message(self, request, obj):
        processing_triggered = (bool(request.FILES.get("video_file")) or bool(request.POST.get("direct_upload_key"))) and obj.is_processing_pending
        if processing_triggered:
            return self._get_processing_change_success_message()
        return self._get_default_change_success_message()

    def _build_submit_guard_key(self, request):
        payload_parts = []
        for key in sorted(request.POST.keys()):
            if key == "csrfmiddlewaretoken":
                continue
            for value in request.POST.getlist(key):
                payload_parts.append(f"{key}={value}")

        for key in sorted(request.FILES.keys()):
            uploaded = request.FILES.get(key)
            if not uploaded:
                continue
            payload_parts.append(
                f"file:{key}={uploaded.name}:{getattr(uploaded, 'size', 0)}"
            )

        for key in (
            "direct_upload_key",
            "direct_upload_original_name",
            "direct_upload_size",
            "direct_upload_content_type",
        ):
            value = request.POST.get(key)
            if value:
                payload_parts.append(f"{key}={value}")

        digest = hashlib.sha256("&".join(payload_parts).encode("utf-8")).hexdigest()
        return f"map_app:admin:video:submit_guard:{request.user.pk}:{digest}"

    def _is_duplicate_add_submit(self, request):
        return not cache.add(self._build_submit_guard_key(request), "1", timeout=20)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        is_add = object_id is None
        if is_add and request.method == "POST" and self._is_duplicate_add_submit(request):
            messages.warning(request, "短時間に同じ動画送信が検出されたため、重複アップロードを防止しました。")
            return redirect(reverse("admin:map_app_video_changelist"))
        return super().changeform_view(request, object_id, form_url, extra_context)

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["show_regenerate_thumbnail"] = self._can_regenerate_thumbnail(obj)
        context["video_status_endpoint"] = reverse("admin:map_app_video_status")
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def direct_upload_url_view(self, request):
        if not settings.USE_S3:
            return JsonResponse({"error": "S3 storage is disabled."}, status=400)
        if request.method != "POST":
            return JsonResponse({"error": "POST only."}, status=405)

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)

        filename = (payload.get("filename") or "").strip()
        content_type = (payload.get("content_type") or "").strip().lower()
        file_size = int(payload.get("size") or 0)
        candidate = _DirectUploadedVideoFile(name=filename, size=file_size, content_type=content_type)
        try:
            validate_video_file(candidate)
        except ValidationError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        if not getattr(default_storage, "bucket_name", None) and not getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""):
            return JsonResponse({"error": "S3 bucket is not configured."}, status=500)

        object_key, relative_key = build_direct_upload_key(filename)
        client = build_s3_client()
        upload_url = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": getattr(default_storage, "bucket_name", None) or settings.AWS_STORAGE_BUCKET_NAME,
                "Key": object_key,
                "ContentType": content_type or "application/octet-stream",
            },
            ExpiresIn=max(300, int(getattr(settings, "VIDEO_DIRECT_UPLOAD_URL_EXPIRES_SECONDS", 7200))),
            HttpMethod="PUT",
        )

        return JsonResponse(
            {
                "upload_url": upload_url,
                "object_key": object_key,
                "relative_key": relative_key,
                "content_type": content_type or "application/octet-stream",
            }
        )

    def status_view(self, request):
        if request.method != "GET":
            return JsonResponse({"error": "GET only."}, status=405)

        video_ids = []
        for raw_id in (request.GET.get("ids") or "").split(","):
            value = (raw_id or "").strip()
            if not value:
                continue
            try:
                video_ids.append(int(value))
            except ValueError:
                continue

        if not video_ids:
            return JsonResponse({"videos": []})

        videos = Video.objects.filter(pk__in=video_ids).order_by("id")
        return JsonResponse({"videos": [self._serialize_video_status(video) for video in videos]})

    @staticmethod
    def _serialize_video_status(video):
        return {
            "id": video.pk,
            "processing_status": video.processing_status,
            "processing_status_display": video.get_processing_status_display(),
            "processing_step_display": video.processing_step_display(),
            "processing_progress_percent": int(getattr(video, "processing_progress_percent", 0) or 0),
            "processing_error": video.processing_error or "",
        }

    def response_add(self, request, obj, post_url_continue=None):
        if self._uses_standard_redirect(request):
            return super().response_add(request, obj, post_url_continue)
        self.message_user(
            request,
            self._get_add_success_message(),
            messages.SUCCESS,
        )
        return self.response_post_save_add(request, obj)

    def response_change(self, request, obj):
        if "_regenerate_thumbnail" in request.POST:
            if not self._can_regenerate_thumbnail(obj):
                self.message_user(
                    request,
                    "サムネイル再作成は、動画処理完了後の動画に対してのみ実行できます。",
                    messages.WARNING,
                )
                return redirect(reverse("admin:map_app_video_change", args=[obj.pk]))

            obj.prepare_thumbnail_regeneration()
            obj.save(update_fields=["processing_status", "processing_error", "thumbnail_regeneration_requested", "processed_at", "updated_at"])
            schedule_video_processing(obj.pk)
            self.message_user(
                request,
                "✔ サムネイル再作成を受け付けました。バックグラウンドで処理します。",
                messages.SUCCESS,
            )
            return redirect(reverse("admin:map_app_video_change", args=[obj.pk]))

        if self._uses_standard_redirect(request):
            return super().response_change(request, obj)
        self.message_user(
            request,
            self._get_change_success_message(request, obj),
            messages.SUCCESS,
        )
        return self.response_post_save_change(request, obj)

    @staticmethod
    def _can_regenerate_thumbnail(obj):
        return bool(
            obj
            and obj.pk
            and obj.video_file
            and not obj.is_processing_pending
            and not obj.is_processing_running
        )
