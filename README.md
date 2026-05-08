# map_app

Domain-switchable shared services for Django map projects.

`map_app` keeps reusable map logic in one place and binds project-specific models/functions via settings.

## Install

```bash
uv add --editable /path/to/map_app
```

or

```bash
pip install -e /path/to/map_app
```

## Django Setup

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "map_app",
]
```

Set required bindings in `config/settings.py`:

```python
MAP_APP_SITE_SETTINGS_MODEL = "piano_map.models.SiteSettings"
MAP_APP_TAG_MODEL = "piano_map.models.Tag"
MAP_APP_LOCATION_MODEL = "piano_map.models.Location"
MAP_APP_ACTIVITY_LOG_MODEL = "piano_map.models.ActivityLog"
MAP_APP_ACTIVITY_LOG_ITEM_MODEL = "piano_map.models.ActivityLogItem"
MAP_APP_LOCATION_PHOTO_MODEL = "piano_map.models.LocationPhoto"
MAP_APP_DOMAIN_FIELD_DEFINITION_MODEL = "piano_map.models.DomainFieldDefinition"
MAP_APP_VIDEO_MODEL = "piano_map.models.Video"
MAP_APP_DEFAULT_DOMAIN_TERMS_FUNC = "piano_map.models.default_domain_terms"
MAP_APP_BUILD_MAP_STATISTICS_FUNC = "piano_map.statistics_service.build_map_statistics"
MAP_APP_MAP_ASSETS_MODULE = "map_app.map_assets"
```

Template/static bindings:

```python
MAP_APP_TEMPLATE_SUMMARY_BOX = "piano_map/summary_box.html"
MAP_APP_TEMPLATE_STATISTICS = "piano_map/statistics.html"
MAP_APP_TEMPLATE_HEADER = "piano_map/header.html"
MAP_APP_TEMPLATE_HAMBURGER_MENU = "piano_map/hamburger_menu.html"
MAP_APP_TEMPLATE_MODALS = "piano_map/modals.html"
MAP_APP_STATIC_PREFIX = "piano_map"
MAP_APP_CACHE_KEY_NAMESPACE = "map_app"
```

System tag bindings:

```python
MAP_APP_SYSTEM_INFO_ONLY_TAG_KEY = "system_info_only_tag_label"
MAP_APP_SYSTEM_INFO_ONLY_TAG_LEGACY_KEY = "system_piano_info_only_tag_label"
```

## What is shared now

- map/search payload contract
- map page rendering services
- tag/query/summary/cache warmup services
- location duplicate detection/merge service
- modal payload builder service
- link preview service
- healthcheck service
- video query/transcode/processing services

## Migration Policy

- `map_app` does not own Django models or migrations.
- Project apps (e.g. `piano_map`) own schema and migrations.
- `map_app` only imports model classes/functions through `MAP_APP_*` bindings.

## Development

Run package regression tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

See [docs/migration_checklist.md](docs/migration_checklist.md) for host-app migration steps.
