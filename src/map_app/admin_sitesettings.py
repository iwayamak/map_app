from django import forms


DOMAIN_TERM_FIELDS = (
    ("app_title", "アプリ名"),
    ("subtitle", "サブタイトル"),
    ("location_label", "場所ラベル"),
    ("record_label", "記録ラベル"),
    ("item_label", "項目ラベル"),
    ("summary_title", "サマリータイトル"),
    ("total_records_label", "総件数ラベル"),
    ("search_placeholder", "検索プレースホルダ"),
    ("search_aria_label", "検索ARIAラベル"),
    ("modal_records_title", "モーダル: 記録セクション名"),
    ("modal_empty_records_text", "モーダル: 空データ文言"),
    ("modal_note_title", "モーダル: メモ見出し"),
    ("modal_count_label", "モーダル: 回数ラベル"),
    ("system_unvisited_tag_label", "システムタグ: 未訪問"),
    ("system_info_only_tag_label", "システムタグ: 情報のみ表示（ドメイン固有）"),
)

DOMAIN_TERM_BOOLEAN_FIELDS = (
    ("show_video_library_menu", "メニュー: 動画ライブラリを表示"),
)

MODAL_PHOTO_PROFILE_CHOICES = (
    ("preserve", "モーダル写真: 全体表示（トリミングしない）"),
    ("fit_width", "モーダル写真: 横幅優先（高さ内に収める）"),
    ("fill", "モーダル写真: ステージ充填（トリミングあり）"),
)

ADMIN_LABEL_FIELDS = (
    ("admin_label_location", "管理画面: 場所"),
    ("admin_label_tag", "管理画面: タグ"),
    ("admin_label_activity_log", "管理画面: 記録"),
    ("admin_label_activity_item", "管理画面: 記録項目マスター"),
    ("admin_label_video", "管理画面: 動画"),
    ("admin_label_site_settings", "管理画面: サイト設定"),
)

MODAL_SECTION_FIELDS = (
    ("modal_section_access_active", "モーダル: アクセス情報"),
    ("modal_section_meta_active", "モーダル: メタ情報（回数/訪問区分）"),
    ("modal_section_detail_note_active", "モーダル: メモ"),
    ("modal_section_records_active", "モーダル: 記録セクション"),
    ("modal_section_tags_active", "モーダル: タグ"),
    ("modal_section_photos_active", "モーダル: 写真"),
)

MODAL_SECTION_KEY_BY_FIELD = {
    "modal_section_access_active": "access",
    "modal_section_meta_active": "meta",
    "modal_section_detail_note_active": "detail_note",
    "modal_section_records_active": "records",
    "modal_section_tags_active": "tags",
    "modal_section_photos_active": "photos",
}


def build_sitesettings_admin(site_settings_model, default_domain_terms_func):
    class SiteSettingsAdminForm(forms.ModelForm):
        _wide_text_widget = forms.TextInput(attrs={"style": "width: min(72ch, 96%);"})
        app_title = forms.CharField(max_length=120, required=False, label="アプリ名", widget=_wide_text_widget)
        subtitle = forms.CharField(max_length=120, required=False, label="サブタイトル", widget=_wide_text_widget)
        location_label = forms.CharField(max_length=40, required=False, label="場所ラベル", widget=_wide_text_widget)
        record_label = forms.CharField(max_length=40, required=False, label="記録ラベル", widget=_wide_text_widget)
        item_label = forms.CharField(max_length=40, required=False, label="項目ラベル", widget=_wide_text_widget)
        summary_title = forms.CharField(max_length=120, required=False, label="サマリータイトル", widget=_wide_text_widget)
        total_records_label = forms.CharField(max_length=120, required=False, label="総件数ラベル", widget=_wide_text_widget)
        search_placeholder = forms.CharField(max_length=200, required=False, label="検索プレースホルダ", widget=_wide_text_widget)
        search_aria_label = forms.CharField(max_length=200, required=False, label="検索ARIAラベル", widget=_wide_text_widget)
        modal_records_title = forms.CharField(max_length=120, required=False, label="モーダル: 記録セクション名", widget=_wide_text_widget)
        modal_empty_records_text = forms.CharField(max_length=120, required=False, label="モーダル: 空データ文言", widget=_wide_text_widget)
        modal_note_title = forms.CharField(max_length=120, required=False, label="モーダル: メモ見出し", widget=_wide_text_widget)
        modal_count_label = forms.CharField(max_length=120, required=False, label="モーダル: 回数ラベル", widget=_wide_text_widget)
        modal_photo_profile = forms.ChoiceField(
            required=False,
            label="モーダル写真: 表示プロファイル",
            choices=MODAL_PHOTO_PROFILE_CHOICES,
            initial="preserve",
        )
        modal_photo_stage_max_height_vh = forms.IntegerField(
            required=False,
            min_value=40,
            max_value=90,
            label="モーダル写真: ステージ最大高さ(vh)",
            initial=70,
        )
        system_unvisited_tag_label = forms.CharField(max_length=40, required=False, label="システムタグ: 未訪問", widget=_wide_text_widget)
        system_info_only_tag_label = forms.CharField(max_length=80, required=False, label="システムタグ: 情報のみ表示（ドメイン固有）", widget=_wide_text_widget)
        show_video_library_menu = forms.BooleanField(required=False, label="メニュー: 動画ライブラリを表示")
        admin_label_location = forms.CharField(max_length=80, required=False, label="管理画面: 場所", widget=_wide_text_widget)
        admin_label_tag = forms.CharField(max_length=80, required=False, label="管理画面: タグ", widget=_wide_text_widget)
        admin_label_activity_log = forms.CharField(max_length=80, required=False, label="管理画面: 記録", widget=_wide_text_widget)
        admin_label_activity_item = forms.CharField(max_length=80, required=False, label="管理画面: 記録項目マスター", widget=_wide_text_widget)
        admin_label_video = forms.CharField(max_length=80, required=False, label="管理画面: 動画", widget=_wide_text_widget)
        admin_label_site_settings = forms.CharField(max_length=80, required=False, label="管理画面: サイト設定", widget=_wide_text_widget)
        modal_section_access_active = forms.BooleanField(required=False, label="モーダル: アクセス情報")
        modal_section_meta_active = forms.BooleanField(required=False, label="モーダル: メタ情報（回数/訪問区分）")
        modal_section_detail_note_active = forms.BooleanField(required=False, label="モーダル: メモ")
        modal_section_records_active = forms.BooleanField(required=False, label="モーダル: 記録セクション")
        modal_section_tags_active = forms.BooleanField(required=False, label="モーダル: タグ")
        modal_section_photos_active = forms.BooleanField(required=False, label="モーダル: 写真")

        class Meta:
            model = site_settings_model
            fields = ("site_title", "site_logo", "favicon")

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            terms = self.instance.get_domain_terms() if self.instance and self.instance.pk else default_domain_terms_func()
            for key, _label in DOMAIN_TERM_FIELDS:
                self.fields[key].initial = terms.get(key, "")
            for key, _label in DOMAIN_TERM_BOOLEAN_FIELDS:
                self.fields[key].initial = bool(terms.get(key, False))
            self.fields["modal_photo_profile"].initial = terms.get("modal_photo_profile", "preserve")
            max_height = terms.get("modal_photo_stage_max_height_vh", 70)
            try:
                max_height = int(max_height)
            except (TypeError, ValueError):
                max_height = 70
            self.fields["modal_photo_stage_max_height_vh"].initial = max(40, min(90, max_height))
            for key, _label in ADMIN_LABEL_FIELDS:
                self.fields[key].initial = terms.get(key, "")
            modal_sections = terms.get("modal_sections", {}) if isinstance(terms.get("modal_sections"), dict) else {}
            for field_name, _label in MODAL_SECTION_FIELDS:
                section_key = MODAL_SECTION_KEY_BY_FIELD[field_name]
                self.fields[field_name].initial = bool(modal_sections.get(section_key, True))

        def clean(self):
            cleaned = super().clean()
            current_terms = self.instance.domain_terms if isinstance(self.instance.domain_terms, dict) else {}
            merged_terms = dict(current_terms)
            defaults = default_domain_terms_func()
            for key, _label in DOMAIN_TERM_FIELDS:
                value = (cleaned.get(key) or "").strip()
                merged_terms[key] = value or defaults.get(key, "")
            # Backward compatibility: keep legacy key synced so old clients/settings still work.
            if merged_terms.get("system_info_only_tag_label"):
                merged_terms["system_piano_info_only_tag_label"] = merged_terms["system_info_only_tag_label"]
            for key, _label in DOMAIN_TERM_BOOLEAN_FIELDS:
                merged_terms[key] = bool(cleaned.get(key))
            photo_profile = (cleaned.get("modal_photo_profile") or "preserve").strip()
            valid_profiles = {key for key, _label in MODAL_PHOTO_PROFILE_CHOICES}
            merged_terms["modal_photo_profile"] = photo_profile if photo_profile in valid_profiles else "preserve"
            stage_max_vh = cleaned.get("modal_photo_stage_max_height_vh")
            try:
                stage_max_vh = int(stage_max_vh if stage_max_vh is not None else 70)
            except (TypeError, ValueError):
                stage_max_vh = 70
            merged_terms["modal_photo_stage_max_height_vh"] = max(40, min(90, stage_max_vh))
            for key, _label in ADMIN_LABEL_FIELDS:
                value = (cleaned.get(key) or "").strip()
                merged_terms[key] = value or defaults.get(key, "")
            default_modal_sections = defaults.get("modal_sections", {})
            merged_modal_sections = dict(default_modal_sections)
            current_modal_sections = merged_terms.get("modal_sections", {})
            if isinstance(current_modal_sections, dict):
                merged_modal_sections.update(current_modal_sections)
            for field_name, _label in MODAL_SECTION_FIELDS:
                section_key = MODAL_SECTION_KEY_BY_FIELD[field_name]
                merged_modal_sections[section_key] = bool(cleaned.get(field_name))
            merged_terms["modal_sections"] = merged_modal_sections
            cleaned["domain_terms"] = merged_terms
            return cleaned

        def save(self, commit=True):
            instance = super().save(commit=False)
            instance.domain_terms = self.cleaned_data["domain_terms"]
            if commit:
                instance.save()
                self.save_m2m()
            return instance

    class SiteSettingsAdminMixin:
        form = SiteSettingsAdminForm

        def has_add_permission(self, request):
            return False

        def has_delete_permission(self, request, obj=None):
            return False

        fieldsets = (
            ("サイト設定", {
                "fields": ("site_title", "site_logo", "favicon"),
                "description": "ヘッダーに表示されるタイトルとロゴ、ブラウザタブに表示されるファビコンを設定できます。",
            }),
            ("表示文言", {
                "fields": tuple(field_name for field_name, _ in DOMAIN_TERM_FIELDS),
                "description": "画面表示の文言を用途に合わせて変更できます。保存時に内部JSONへ変換して保持します。",
            }),
            ("メニュー表示制御", {
                "fields": tuple(field_name for field_name, _ in DOMAIN_TERM_BOOLEAN_FIELDS),
                "description": "ハンバーガーメニュー項目の表示/非表示を切り替えます。",
            }),
            ("モーダル写真表示", {
                "fields": ("modal_photo_profile", "modal_photo_stage_max_height_vh"),
                "description": "写真を切り抜かず表示するか、横幅優先にするか、ステージ充填するかを選べます。",
            }),
            ("管理画面表示名", {
                "fields": tuple(field_name for field_name, _ in ADMIN_LABEL_FIELDS),
                "description": "管理画面メニューの表示名を用途に合わせて変更できます。",
            }),
            ("モーダル表示制御", {
                "fields": tuple(field_name for field_name, _ in MODAL_SECTION_FIELDS),
                "description": "モーダル内の各セクションをドメインごとにON/OFFできます。",
            }),
        )

    return SiteSettingsAdminMixin
