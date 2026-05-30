import re

from django import forms
from django.contrib import admin

from .models import DomainFieldDefinition


class DomainFieldDefinitionAdminForm(forms.ModelForm):
    TARGET_LABELS = {
        DomainFieldDefinition.TARGET_LOCATION: "場所に追加",
        DomainFieldDefinition.TARGET_ACTIVITY_LOG: "記録に追加",
    }

    key = forms.CharField(
        label="内部ID（英数字）",
        help_text="通常は「表示名から自動生成」でOKです。例: stamp_type, visit_season, goshuin_note",
        widget=forms.TextInput(
            attrs={
                "placeholder": "stamp_type",
                "data-key-suggestions": "stamp_type,visit_season,goshuin_note",
            }
        ),
    )
    choices_text = forms.CharField(
        label="選択肢（1行1つ）",
        required=False,
        help_text="型が「単一選択 / 複数選択」のときに入力します。例: 初級↵中級↵上級",
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": "初級\n中級\n上級",
            }
        ),
    )

    class Meta:
        model = DomainFieldDefinition
        fields = (
            "target",
            "label",
            "key",
            "field_type",
            "choices_text",
            "is_required",
            "order",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target"].choices = [
            (value, self.TARGET_LABELS.get(value, label))
            for value, label in self.fields["target"].choices
        ]
        existing_choices = self.instance.choices_json if self.instance and isinstance(self.instance.choices_json, list) else []
        self.fields["choices_text"].initial = "\n".join(existing_choices)

    def clean_key(self):
        value = (self.cleaned_data.get("key") or "").strip().lower()
        if not re.fullmatch(r"[a-z][a-z0-9_]*", value):
            raise forms.ValidationError("半角英小文字で開始、英小文字/数字/_ のみで入力してください。")
        return value

    def clean(self):
        cleaned = super().clean()
        field_type = cleaned.get("field_type")
        lines = (cleaned.get("choices_text") or "").splitlines()
        choices = [line.strip() for line in lines if line.strip()]
        if field_type in {DomainFieldDefinition.TYPE_SELECT, DomainFieldDefinition.TYPE_MULTISELECT}:
            if not choices:
                self.add_error("choices_text", "選択型では1つ以上の選択肢を入力してください。")
            cleaned["choices_json"] = choices
        else:
            cleaned["choices_json"] = []
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.choices_json = self.cleaned_data.get("choices_json", [])
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class DomainFieldDefinitionAdmin(admin.ModelAdmin):
    form = DomainFieldDefinitionAdminForm
    list_display = ("target", "label", "key", "field_type", "is_required", "is_active", "order")
    list_filter = ("target", "field_type", "is_required", "is_active")
    search_fields = ("label", "key")
    ordering = ("target", "order", "id")

    class Media:
        js = ("map_app/js/admin_domain_field.js?v=1",)
