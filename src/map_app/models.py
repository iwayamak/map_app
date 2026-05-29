from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string

from map_app.base_models import (
    BaseActivityItem,
    BaseActivityLog,
    BaseActivityLogItem,
    BaseDomainFieldDefinition,
    BaseLocation,
    BaseLocationPhoto,
    BaseSiteSettings,
    BaseTag,
    BaseVideo,
)
from map_app.model_behaviors import (
    ActivityLogBehavior,
    DomainFieldDefinitionBehavior,
    LocationBehavior,
    LocationPhotoBehavior,
    SiteSettingsBehavior,
    TagBehavior,
    VideoBehavior,
)


def _optional_setting_callable(setting_name):
    dotted_path = getattr(settings, setting_name, "")
    if not dotted_path:
        return None
    return import_string(dotted_path)


def _compress_uploaded_image(image, *, max_width, max_height, quality, output_format):
    compressor = _optional_setting_callable("MAP_APP_COMPRESS_UPLOADED_IMAGE_FUNC")
    if compressor is None:
        return image
    return compressor(
        image,
        max_width=max_width,
        max_height=max_height,
        quality=quality,
        output_format=output_format,
    )


def _schedule_video_processing(video_id):
    scheduler = _optional_setting_callable("MAP_APP_SCHEDULE_VIDEO_PROCESSING_FUNC")
    if scheduler is None:
        return None
    return scheduler(video_id)


def default_site_title():
    return getattr(settings, "MAP_APP_SITE_TITLE_DEFAULT", "")


def default_domain_terms():
    terms_loader = _optional_setting_callable("MAP_APP_DEFAULT_DOMAIN_TERMS_FUNC")
    if terms_loader is None:
        return {}
    return terms_loader()


class SiteSettings(SiteSettingsBehavior, BaseSiteSettings):
    site_title = models.CharField(max_length=100, default=default_site_title, verbose_name="サイトタイトル")
    site_logo = models.ImageField(
        upload_to="site/",
        blank=True,
        null=True,
        verbose_name="サイトロゴ",
        help_text="ヘッダーに表示されるロゴ画像",
    )
    favicon = models.ImageField(
        upload_to="site/",
        blank=True,
        null=True,
        verbose_name="ファビコン",
        help_text="ブラウザタブに表示されるアイコン（推奨: 32x32px または 64x64px の正方形画像）",
    )
    domain_terms = models.JSONField(
        default=default_domain_terms,
        blank=True,
        verbose_name="ドメイン語彙",
        help_text="UI文言を差し替えるための辞書（例: 御朱印マップ向け）。",
    )

    class Meta:
        db_table = "piano_map_sitesettings"
        verbose_name = "サイト設定"
        verbose_name_plural = "サイト設定"

    def __str__(self):
        return "サイト設定"

    _compress_uploaded_image = staticmethod(_compress_uploaded_image)


class Tag(TagBehavior, BaseTag):
    class Meta:
        db_table = "piano_map_tag"
        verbose_name = "タグ"
        verbose_name_plural = "タグ"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Location(LocationBehavior, BaseLocation):
    tags = models.ManyToManyField(
        "map_app.Tag",
        blank=True,
        db_table="piano_map_location_tags",
        related_name="locations",
        verbose_name="タグ",
    )

    class Meta:
        db_table = "piano_map_location"
        verbose_name = "場所"
        verbose_name_plural = "場所"
        ordering = ["name"]

    def __str__(self):
        return self.name

    _compress_uploaded_image = staticmethod(_compress_uploaded_image)


class LocationPhoto(LocationPhotoBehavior, BaseLocationPhoto):
    location = models.ForeignKey(
        "map_app.Location",
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name="場所",
    )
    image = models.ImageField(upload_to="location_photos/", verbose_name="写真")
    thumbnail_small = models.ImageField(
        upload_to="location_photos/thumbs/",
        blank=True,
        null=True,
        verbose_name="サムネイル(小)",
    )
    thumbnail_medium = models.ImageField(
        upload_to="location_photos/thumbs/",
        blank=True,
        null=True,
        verbose_name="サムネイル(中)",
    )

    class Meta:
        db_table = "piano_map_locationphoto"
        verbose_name = "場所写真"
        verbose_name_plural = "場所写真"
        ordering = ["order", "id"]
        indexes = [
            models.Index(fields=["location", "order"], name="piano_map_l_locatio_de1fb4_idx"),
        ]

    def __str__(self):
        return f"{self.location.name} - 写真{self.id}"

    _compress_uploaded_image = staticmethod(_compress_uploaded_image)


class ActivityItem(BaseActivityItem):
    class Meta:
        db_table = "piano_map_activityitem"
        verbose_name = "記録項目マスター"
        verbose_name_plural = "記録項目マスター"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ActivityLog(ActivityLogBehavior, BaseActivityLog):
    location = models.ForeignKey(
        "map_app.Location",
        on_delete=models.CASCADE,
        related_name="activity_logs",
        verbose_name="場所",
    )

    class Meta:
        db_table = "piano_map_activitylog"
        verbose_name = "記録"
        verbose_name_plural = "記録"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["date"], name="piano_map_a_date_0b5782_idx"),
            models.Index(fields=["location", "date"], name="piano_map_a_locatio_be02cf_idx"),
        ]

    def __str__(self):
        if self.title:
            return f"{self.location.name} - {self.title} ({self.date})"
        return f"{self.location.name} ({self.date})"


class ActivityLogItem(BaseActivityLogItem):
    activity_log = models.ForeignKey(
        "map_app.ActivityLog",
        on_delete=models.CASCADE,
        verbose_name="汎用記録",
    )
    item = models.ForeignKey(
        "map_app.ActivityItem",
        on_delete=models.CASCADE,
        verbose_name="項目",
    )

    class Meta:
        db_table = "piano_map_activitylogitem"
        verbose_name = "記録項目"
        verbose_name_plural = "記録項目"
        ordering = ["order"]
        unique_together = ["activity_log", "item"]
        indexes = [
            models.Index(fields=["activity_log", "order"], name="piano_map_a_activit_1a65e6_idx"),
        ]

    def __str__(self):
        return f"{self.activity_log.location.name} ({self.activity_log.date}) - {self.item.name}"


class DomainFieldDefinition(DomainFieldDefinitionBehavior, BaseDomainFieldDefinition):
    class Meta:
        db_table = "piano_map_domainfielddefinition"
        verbose_name = "追加項目テンプレート"
        verbose_name_plural = "追加項目テンプレート"
        ordering = ["target", "order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["target", "key"], name="uq_domainfield_target_key"),
        ]

    def __str__(self):
        return f"{self.get_target_display()}:{self.label} ({self.key})"


class Video(VideoBehavior, BaseVideo):
    video_file = models.FileField(upload_to="videos/", verbose_name="動画ファイル")
    thumbnail = models.ImageField(upload_to="videos/thumbs/", blank=True, null=True, verbose_name="サムネイル")

    class Meta:
        db_table = "piano_map_video"
        verbose_name = "動画"
        verbose_name_plural = "動画"
        ordering = ["-is_featured", "featured_order", "-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["is_published", "-published_at"], name="piano_map_v_is_publ_25f9c0_idx"),
            models.Index(fields=["is_featured", "featured_order"], name="piano_map_v_is_feat_9ed0f8_idx"),
        ]

    def __str__(self):
        return self.title

    def _schedule_video_processing(self, video_id):
        _schedule_video_processing(video_id)
