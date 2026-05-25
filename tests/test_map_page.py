from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from map_app.map_page import (
    get_css_styles,
    get_header_background,
    get_theme_color,
    normalize_document_meta,
)


class MapPageThemeTests(TestCase):
    def test_get_theme_color_uses_solid_header_color(self):
        site_settings = SimpleNamespace(
            get_domain_terms=lambda: {
                "header_bg_mode": "solid",
                "header_bg_solid_color": "#123456",
                "header_bg_gradient_from": "#abcdef",
            }
        )

        self.assertEqual(get_theme_color(site_settings), "#123456")

    def test_get_theme_color_uses_gradient_start_color(self):
        site_settings = SimpleNamespace(
            get_domain_terms=lambda: {
                "header_bg_mode": "gradient",
                "header_bg_solid_color": "#123456",
                "header_bg_gradient_from": "#abcdef",
            }
        )

        self.assertEqual(get_theme_color(site_settings), "#abcdef")

    def test_get_header_background_uses_full_gradient(self):
        site_settings = SimpleNamespace(
            get_domain_terms=lambda: {
                "header_bg_mode": "gradient",
                "header_bg_gradient_from": "#abcdef",
                "header_bg_gradient_to": "#123456",
                "header_bg_gradient_angle": 90,
            }
        )

        self.assertEqual(
            get_header_background(site_settings),
            "linear-gradient(90deg, #abcdef 0%, #123456 100%)",
        )

    def test_normalize_document_meta_replaces_viewport_and_theme_color(self):
        html = (
            "<html><head>"
            '<meta name="viewport" content="width=device-width">'
            '<meta name="theme-color" content="#000000">'
            "</head><body></body></html>"
        )

        normalized = normalize_document_meta(html, "#123456")

        self.assertIn("viewport-fit=cover", normalized)
        self.assertIn('<meta name="theme-color" content="#123456" />', normalized)
        self.assertEqual(normalized.count('name="viewport"'), 1)
        self.assertEqual(normalized.count('name="theme-color"'), 1)

    def test_get_css_styles_sets_viewport_theme_color_and_body_background(self):
        site_settings = SimpleNamespace(
            favicon=None,
            get_domain_terms=lambda: {
                "header_bg_mode": "solid",
                "header_bg_solid_color": "#123456",
            },
        )

        with patch("map_app.map_page.map_css_link_tags", return_value=""):
            css = get_css_styles(site_settings)

        self.assertIn("viewport-fit=cover", css)
        self.assertIn('<meta name="theme-color" content="#123456" />', css)
        self.assertIn("--map-safe-area-bg: #123456;", css)
        self.assertIn("background: #123456 !important;", css)

    def test_get_css_styles_defines_safe_area_after_css_links(self):
        site_settings = SimpleNamespace(
            favicon=None,
            get_domain_terms=lambda: {
                "header_bg_mode": "gradient",
                "header_bg_gradient_from": "#abcdef",
                "header_bg_gradient_to": "#123456",
                "header_bg_gradient_angle": 90,
            },
        )

        with patch("map_app.map_page.map_css_link_tags", return_value='<link rel="stylesheet" href="/static/map.css" />'):
            css = get_css_styles(site_settings)

        self.assertLess(css.index("/static/map.css"), css.index("--map-safe-area-bg"))
        self.assertIn("--map-safe-area-bg: linear-gradient(90deg, #abcdef 0%, #123456 100%);", css)
