import map_app.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="ActivityItem",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("name", models.CharField(max_length=200, unique=True, verbose_name="項目名")),
                        ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="登録日時")),
                    ],
                    options={
                        "verbose_name": "記録項目マスター",
                        "verbose_name_plural": "記録項目マスター",
                        "db_table": "piano_map_activityitem",
                        "ordering": ["name"],
                    },
                ),
                migrations.CreateModel(
                    name="DomainFieldDefinition",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        (
                            "target",
                            models.CharField(
                                choices=[("location", "場所"), ("activity_log", "記録")],
                                db_index=True,
                                max_length=24,
                                verbose_name="対象",
                            ),
                        ),
                        ("key", models.CharField(max_length=64, verbose_name="キー")),
                        ("label", models.CharField(max_length=120, verbose_name="表示名")),
                        (
                            "field_type",
                            models.CharField(
                                choices=[
                                    ("text", "テキスト"),
                                    ("number", "数値"),
                                    ("date", "日付"),
                                    ("boolean", "真偽値"),
                                    ("select", "単一選択"),
                                    ("multiselect", "複数選択"),
                                ],
                                default="text",
                                max_length=24,
                                verbose_name="型",
                            ),
                        ),
                        ("is_required", models.BooleanField(default=False, verbose_name="必須")),
                        (
                            "choices_json",
                            models.JSONField(
                                blank=True,
                                default=list,
                                help_text="管理画面では1行1選択肢入力を使用します。",
                                verbose_name="選択肢データ",
                            ),
                        ),
                        ("order", models.PositiveIntegerField(db_index=True, default=0, verbose_name="表示順")),
                        ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="有効")),
                        ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="作成日時")),
                        ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新日時")),
                    ],
                    options={
                        "verbose_name": "追加項目テンプレート",
                        "verbose_name_plural": "追加項目テンプレート",
                        "db_table": "piano_map_domainfielddefinition",
                        "ordering": ["target", "order", "id"],
                    },
                ),
                migrations.CreateModel(
                    name="SiteSettings",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        (
                            "site_title",
                            models.CharField(default=map_app.models.default_site_title, max_length=100, verbose_name="サイトタイトル"),
                        ),
                        (
                            "site_logo",
                            models.ImageField(
                                blank=True,
                                help_text="ヘッダーに表示されるロゴ画像",
                                null=True,
                                upload_to="site/",
                                verbose_name="サイトロゴ",
                            ),
                        ),
                        (
                            "favicon",
                            models.ImageField(
                                blank=True,
                                help_text="ブラウザタブに表示されるアイコン（推奨: 32x32px または 64x64px の正方形画像）",
                                null=True,
                                upload_to="site/",
                                verbose_name="ファビコン",
                            ),
                        ),
                        (
                            "domain_terms",
                            models.JSONField(
                                blank=True,
                                default=map_app.models.default_domain_terms,
                                help_text="UI文言を差し替えるための辞書（例: 御朱印マップ向け）。",
                                verbose_name="ドメイン語彙",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "サイト設定",
                        "verbose_name_plural": "サイト設定",
                        "db_table": "piano_map_sitesettings",
                    },
                ),
                migrations.CreateModel(
                    name="Tag",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("name", models.CharField(db_index=True, max_length=50, unique=True, verbose_name="タグ名")),
                        ("color", models.CharField(editable=False, max_length=7, unique=True, verbose_name="チップ色")),
                        ("order", models.PositiveIntegerField(db_index=True, default=0, verbose_name="表示順")),
                        ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="作成日時")),
                    ],
                    options={
                        "verbose_name": "タグ",
                        "verbose_name_plural": "タグ",
                        "db_table": "piano_map_tag",
                        "ordering": ["order", "name"],
                    },
                ),
                migrations.CreateModel(
                    name="Location",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("name", models.CharField(max_length=200, unique=True, verbose_name="場所名")),
                        ("latitude", models.FloatField(verbose_name="緯度")),
                        ("longitude", models.FloatField(verbose_name="経度")),
                        ("nearest_station", models.CharField(blank=True, max_length=120, verbose_name="最寄駅")),
                        ("walking_minutes", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="徒歩分")),
                        ("playable_schedule_note", models.TextField(blank=True, verbose_name="利用可能期間メモ")),
                        ("detail_note", models.TextField(blank=True, verbose_name="詳細メモ")),
                        (
                            "custom_data",
                            models.JSONField(
                                blank=True,
                                default=dict,
                                help_text="ドメイン定義に応じた追加項目データ（JSON）",
                                verbose_name="カスタムデータ",
                            ),
                        ),
                        ("image", models.ImageField(blank=True, null=True, upload_to="photos/", verbose_name="写真")),
                        (
                            "tags",
                            models.ManyToManyField(
                                blank=True,
                                db_table="piano_map_location_tags",
                                related_name="locations",
                                to="map_app.tag",
                                verbose_name="タグ",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "場所",
                        "verbose_name_plural": "場所",
                        "db_table": "piano_map_location",
                        "ordering": ["name"],
                    },
                ),
                migrations.CreateModel(
                    name="Video",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("title", models.CharField(max_length=200, verbose_name="タイトル")),
                        ("description", models.TextField(blank=True, verbose_name="説明")),
                        ("video_file", models.FileField(upload_to="videos/", verbose_name="動画ファイル")),
                        ("thumbnail", models.ImageField(blank=True, null=True, upload_to="videos/thumbs/", verbose_name="サムネイル")),
                        ("is_published", models.BooleanField(db_index=True, default=False, verbose_name="公開")),
                        ("is_featured", models.BooleanField(db_index=True, default=False, verbose_name="おすすめ表示")),
                        ("featured_order", models.PositiveIntegerField(blank=True, db_index=True, null=True, verbose_name="おすすめ順")),
                        (
                            "processing_status",
                            models.CharField(
                                choices=[
                                    ("pending", "処理待ち"),
                                    ("running", "処理中"),
                                    ("ready", "完了"),
                                    ("failed", "失敗"),
                                ],
                                db_index=True,
                                default="ready",
                                max_length=16,
                                verbose_name="処理状態",
                            ),
                        ),
                        ("processing_step", models.CharField(blank=True, default="", max_length=32, verbose_name="処理段階")),
                        ("processing_progress_percent", models.PositiveSmallIntegerField(default=100, verbose_name="進捗率")),
                        ("processing_error", models.TextField(blank=True, verbose_name="処理エラー")),
                        (
                            "thumbnail_regeneration_requested",
                            models.BooleanField(db_index=True, default=False, editable=False, verbose_name="サムネイル再生成待ち"),
                        ),
                        ("video_width", models.PositiveIntegerField(blank=True, null=True, verbose_name="動画幅")),
                        ("video_height", models.PositiveIntegerField(blank=True, null=True, verbose_name="動画高さ")),
                        ("processed_at", models.DateTimeField(blank=True, null=True, verbose_name="処理完了日時")),
                        ("published_at", models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="公開日時")),
                        ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="作成日時")),
                        ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新日時")),
                    ],
                    options={
                        "verbose_name": "動画",
                        "verbose_name_plural": "動画",
                        "db_table": "piano_map_video",
                        "ordering": ["-is_featured", "featured_order", "-published_at", "-created_at"],
                    },
                ),
                migrations.CreateModel(
                    name="ActivityLog",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("title", models.CharField(blank=True, default="", max_length=200, verbose_name="記録タイトル（任意）")),
                        ("date", models.DateField(verbose_name="記録日")),
                        (
                            "custom_data",
                            models.JSONField(
                                blank=True,
                                default=dict,
                                help_text="ドメイン定義に応じた追加項目データ（JSON）",
                                verbose_name="カスタムデータ",
                            ),
                        ),
                        ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="作成日時")),
                        (
                            "location",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="activity_logs",
                                to="map_app.location",
                                verbose_name="場所",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "記録",
                        "verbose_name_plural": "記録",
                        "db_table": "piano_map_activitylog",
                        "ordering": ["-date", "-created_at"],
                    },
                ),
                migrations.CreateModel(
                    name="LocationPhoto",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("image", models.ImageField(upload_to="location_photos/", verbose_name="写真")),
                        ("thumbnail_small", models.ImageField(blank=True, null=True, upload_to="location_photos/thumbs/", verbose_name="サムネイル(小)")),
                        ("thumbnail_medium", models.ImageField(blank=True, null=True, upload_to="location_photos/thumbs/", verbose_name="サムネイル(中)")),
                        ("order", models.PositiveIntegerField(default=0, verbose_name="表示順")),
                        ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="作成日時")),
                        (
                            "location",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="photos",
                                to="map_app.location",
                                verbose_name="場所",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "場所写真",
                        "verbose_name_plural": "場所写真",
                        "db_table": "piano_map_locationphoto",
                        "ordering": ["order", "id"],
                    },
                ),
                migrations.CreateModel(
                    name="ActivityLogItem",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("order", models.PositiveIntegerField(default=0, verbose_name="順序")),
                        (
                            "activity_log",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="map_app.activitylog",
                                verbose_name="汎用記録",
                            ),
                        ),
                        (
                            "item",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="map_app.activityitem",
                                verbose_name="項目",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "記録項目",
                        "verbose_name_plural": "記録項目",
                        "db_table": "piano_map_activitylogitem",
                        "ordering": ["order"],
                        "unique_together": {("activity_log", "item")},
                    },
                ),
                migrations.AddConstraint(
                    model_name="domainfielddefinition",
                    constraint=models.UniqueConstraint(fields=("target", "key"), name="uq_domainfield_target_key"),
                ),
                migrations.AddIndex(
                    model_name="video",
                    index=models.Index(fields=["is_published", "-published_at"], name="piano_map_v_is_publ_25f9c0_idx"),
                ),
                migrations.AddIndex(
                    model_name="video",
                    index=models.Index(fields=["is_featured", "featured_order"], name="piano_map_v_is_feat_9ed0f8_idx"),
                ),
                migrations.AddIndex(
                    model_name="activitylog",
                    index=models.Index(fields=["date"], name="piano_map_a_date_0b5782_idx"),
                ),
                migrations.AddIndex(
                    model_name="activitylog",
                    index=models.Index(fields=["location", "date"], name="piano_map_a_locatio_be02cf_idx"),
                ),
                migrations.AddIndex(
                    model_name="locationphoto",
                    index=models.Index(fields=["location", "order"], name="piano_map_l_locatio_de1fb4_idx"),
                ),
                migrations.AddIndex(
                    model_name="activitylogitem",
                    index=models.Index(fields=["activity_log", "order"], name="piano_map_a_activit_1a65e6_idx"),
                ),
            ],
        ),
    ]
