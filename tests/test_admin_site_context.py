from map_app.admin_site_context import build_admin_header_background, hide_shared_admin_app_entries


def test_hide_shared_admin_app_entries_removes_map_app():
    app_list = [
        {"app_label": "auth", "name": "Authentication"},
        {"app_label": "map_app", "name": "Map App"},
        {"app_label": "piano_map", "name": "Map"},
    ]

    filtered = hide_shared_admin_app_entries(app_list)

    assert [app["app_label"] for app in filtered] == ["auth", "piano_map"]


def test_hide_shared_admin_app_entries_returns_empty_for_map_app_app_label():
    app_list = [{"app_label": "map_app", "name": "Map App"}]

    assert hide_shared_admin_app_entries(app_list, app_label="map_app") == []


def test_build_admin_header_background_returns_solid_color():
    background = build_admin_header_background(
        {
            "header_bg_mode": "solid",
            "header_bg_solid_color": "#123456",
        }
    )

    assert background == "#123456"


def test_build_admin_header_background_returns_gradient():
    background = build_admin_header_background(
        {
            "header_bg_mode": "gradient",
            "header_bg_gradient_angle": 90,
            "header_bg_gradient_from": "#abcdef",
            "header_bg_gradient_to": "#123456",
        }
    )

    assert background == "linear-gradient(90deg, #abcdef 0%, #123456 100%)"


def test_build_admin_header_background_falls_back_to_default_angle():
    background = build_admin_header_background(
        {
            "header_bg_mode": "gradient",
            "header_bg_gradient_angle": "invalid",
            "header_bg_gradient_from": "#abcdef",
            "header_bg_gradient_to": "#123456",
        }
    )

    assert background == "linear-gradient(135deg, #abcdef 0%, #123456 100%)"
