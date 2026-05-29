from map_app.admin_site_context import hide_shared_admin_app_entries


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
