import csv
import io
from datetime import datetime

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html


# 管理画面のタイトルをカスタマイズ
admin.site.site_header = 'すーさんマップ 管理画面'
admin.site.site_title = 'すーさんマップ'
admin.site.index_title = 'ダッシュボード'


def build_csv_response(filename_prefix, header, rows):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename={filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )
    response.write('\ufeff')  # BOM for Excel

    writer = csv.writer(response)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return response


def decode_uploaded_csv(csv_file):
    if not csv_file:
        raise ValueError('CSVファイルを選択してください')
    if not csv_file.name.lower().endswith('.csv'):
        raise ValueError('CSVファイルをアップロードしてください')

    decoded_file = csv_file.read().decode('utf-8-sig')
    return csv.DictReader(io.StringIO(decoded_file))


class CsvAdminMixin:
    csv_import_url_name = None
    csv_export_url_name = None

    def get_simple_list_tools(self, request):
        tools = []
        parent_getter = getattr(super(), "get_simple_list_tools", None)
        if callable(parent_getter):
            tools.extend(parent_getter(request) or [])

        export_name = self.csv_export_url_name or f'{self.model._meta.model_name}_export_all_csv'
        tools.append({
            'url': reverse(f'admin:{export_name}'),
            'label': '全件エクスポート',
            'css_class': 'historylink',
        })
        return tools

    def export_all_as_csv(self, request, queryset):
        """全件CSVエクスポート（アクション用）"""
        return self.export_as_csv(request, self.model.objects.all())

    export_all_as_csv.short_description = '📥 全件CSVエクスポート（全データ）'

    def export_all_csv(self, request):
        """全件CSVエクスポート"""
        return self.export_as_csv(request, self.model.objects.all())

    def get_urls(self):
        custom_urls = [
            path(
                'import-csv/',
                self.admin_site.admin_view(self.import_csv),
                name=self.csv_import_url_name or f'{self.model._meta.model_name}_import_csv',
            ),
            path(
                'export-csv/',
                self.admin_site.admin_view(self.export_all_csv),
                name=self.csv_export_url_name or f'{self.model._meta.model_name}_export_all_csv',
            ),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_export_all'] = True
        return super().changelist_view(request, extra_context=extra_context)


class SimpleDeleteListAdminMixin:
    """Simple changelist behavior: no bulk actions + row-level delete button."""

    actions = None
    delete_button_css_class = 'admin-delete-x'
    change_list_template = 'admin/map_app/shared/simple_list_change_list.html'

    def get_simple_list_tools(self, request):
        return []

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.setdefault('simple_list_tools', self.get_simple_list_tools(request))
        return super().changelist_view(request, extra_context=extra_context)

    def get_actions(self, request):
        return {}

    def get_delete_button_label(self, obj):
        return getattr(obj, 'name', str(obj))

    def delete_button(self, obj):
        delete_url = reverse(
            f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_delete',
            args=[obj.pk],
        )
        return format_html(
            "<a href='{}' class='{}' aria-label='{} を削除' title='削除'>×</a>",
            delete_url,
            self.delete_button_css_class,
            self.get_delete_button_label(obj),
        )

    delete_button.short_description = ''
