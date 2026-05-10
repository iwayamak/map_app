from django.db import models


class BaseSiteSettings(models.Model):
    site_title = models.CharField(max_length=100, verbose_name="サイトタイトル")
    site_logo = models.ImageField(upload_to="site/", blank=True, null=True, verbose_name="サイトロゴ")
    favicon = models.ImageField(upload_to="site/", blank=True, null=True, verbose_name="ファビコン")
    domain_terms = models.JSONField(default=dict, blank=True, verbose_name="ドメイン語彙")

    class Meta:
        abstract = True


class BaseTag(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="タグ名")
    color = models.CharField(max_length=7, unique=True, editable=False, verbose_name="チップ色")
    order = models.PositiveIntegerField(default=0, db_index=True, verbose_name="表示順")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        abstract = True
        ordering = ["order", "name"]


class BaseLocation(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="場所名")
    latitude = models.FloatField(verbose_name="緯度")
    longitude = models.FloatField(verbose_name="経度")
    nearest_station = models.CharField(max_length=120, blank=True, verbose_name="最寄駅")
    walking_minutes = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="徒歩分")
    playable_schedule_note = models.TextField(blank=True, verbose_name="利用可能期間メモ")
    detail_note = models.TextField(blank=True, verbose_name="詳細メモ")
    custom_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="カスタムデータ",
        help_text="ドメイン定義に応じた追加項目データ（JSON）",
    )
    image = models.ImageField(upload_to="photos/", blank=True, null=True, verbose_name="写真")

    class Meta:
        abstract = True
        ordering = ["name"]


class BaseLocationPhoto(models.Model):
    image = models.ImageField(upload_to="photos/", verbose_name="写真")
    thumbnail_small = models.ImageField(upload_to="photos/thumbs/small/", blank=True, null=True, verbose_name="小サムネイル")
    thumbnail_medium = models.ImageField(upload_to="photos/thumbs/medium/", blank=True, null=True, verbose_name="中サムネイル")
    order = models.PositiveIntegerField(default=0, verbose_name="表示順")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        abstract = True


class BaseActivityItem(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="項目名")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")

    class Meta:
        abstract = True
        ordering = ["name"]


class BaseActivityLog(models.Model):
    title = models.CharField(max_length=200, blank=True, default="", verbose_name="記録タイトル（任意）")
    date = models.DateField(verbose_name="記録日")
    custom_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="カスタムデータ",
        help_text="ドメイン定義に応じた追加項目データ（JSON）",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        abstract = True
        ordering = ["-date", "-created_at"]


class BaseActivityLogItem(models.Model):
    order = models.PositiveIntegerField(default=0, verbose_name="順序")

    class Meta:
        abstract = True
        ordering = ["order"]


class BaseDomainFieldDefinition(models.Model):
    TARGET_LOCATION = "location"
    TARGET_ACTIVITY_LOG = "activity_log"
    TARGET_CHOICES = (
        (TARGET_LOCATION, "場所"),
        (TARGET_ACTIVITY_LOG, "記録"),
    )

    TYPE_TEXT = "text"
    TYPE_NUMBER = "number"
    TYPE_DATE = "date"
    TYPE_BOOLEAN = "boolean"
    TYPE_SELECT = "select"
    TYPE_MULTISELECT = "multiselect"
    FIELD_TYPE_CHOICES = (
        (TYPE_TEXT, "テキスト"),
        (TYPE_NUMBER, "数値"),
        (TYPE_DATE, "日付"),
        (TYPE_BOOLEAN, "真偽値"),
        (TYPE_SELECT, "単一選択"),
        (TYPE_MULTISELECT, "複数選択"),
    )

    target = models.CharField(max_length=24, choices=TARGET_CHOICES, db_index=True, verbose_name="対象")
    key = models.CharField(max_length=64, verbose_name="キー")
    label = models.CharField(max_length=120, verbose_name="表示名")
    field_type = models.CharField(max_length=24, choices=FIELD_TYPE_CHOICES, default=TYPE_TEXT, verbose_name="型")
    is_required = models.BooleanField(default=False, verbose_name="必須")
    choices_json = models.JSONField(
        default=list,
        blank=True,
        verbose_name="選択肢データ",
        help_text="管理画面では1行1選択肢入力を使用します。",
    )
    order = models.PositiveIntegerField(default=0, db_index=True, verbose_name="表示順")
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="有効")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        abstract = True


class BaseVideo(models.Model):
    PROCESSING_PENDING = "pending"
    PROCESSING_RUNNING = "running"
    PROCESSING_READY = "ready"
    PROCESSING_FAILED = "failed"
    PROCESSING_CHOICES = (
        (PROCESSING_PENDING, "処理待ち"),
        (PROCESSING_RUNNING, "処理中"),
        (PROCESSING_READY, "完了"),
        (PROCESSING_FAILED, "失敗"),
    )

    title = models.CharField(max_length=200, verbose_name="タイトル")
    description = models.TextField(blank=True, verbose_name="説明")
    video_file = models.FileField(upload_to="videos/", verbose_name="動画ファイル")
    thumbnail = models.ImageField(upload_to="videos/thumbs/", blank=True, null=True, verbose_name="サムネイル")
    is_published = models.BooleanField(default=False, db_index=True, verbose_name="公開")
    is_featured = models.BooleanField(default=False, db_index=True, verbose_name="おすすめ表示")
    featured_order = models.PositiveIntegerField(blank=True, null=True, db_index=True, verbose_name="おすすめ順")
    processing_status = models.CharField(
        max_length=16,
        choices=PROCESSING_CHOICES,
        default=PROCESSING_READY,
        db_index=True,
        verbose_name="処理状態",
    )
    processing_step = models.CharField(max_length=32, blank=True, default="", verbose_name="処理段階")
    processing_progress_percent = models.PositiveSmallIntegerField(default=100, verbose_name="進捗率")
    processing_error = models.TextField(blank=True, verbose_name="処理エラー")
    thumbnail_regeneration_requested = models.BooleanField(
        default=False,
        db_index=True,
        editable=False,
        verbose_name="サムネイル再生成待ち",
    )
    video_width = models.PositiveIntegerField(blank=True, null=True, verbose_name="動画幅")
    video_height = models.PositiveIntegerField(blank=True, null=True, verbose_name="動画高さ")
    processed_at = models.DateTimeField(blank=True, null=True, verbose_name="処理完了日時")
    published_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name="公開日時")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        abstract = True
