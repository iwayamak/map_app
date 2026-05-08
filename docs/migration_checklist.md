# map_app Migration Checklist

This checklist is for migrating a host Django app (for example `piano_map`) onto `map_app`.

1. Add `map_app` to `INSTALLED_APPS`.
2. Set all required `MAP_APP_*` bindings in project settings.
3. Keep models and migrations in the host app; do not move schema into `map_app`.
4. Switch host `services/`, `cache_keys`, `contracts`, and `map_page` to thin wrappers over `map_app`.
5. Keep host-specific compatibility wrappers where tests patch host module paths.
6. Run:
   - `python manage.py check`
   - host map view/API test suite
   - host video processing test suite
7. Verify production settings include `MAP_APP_SYSTEM_INFO_ONLY_TAG_KEY` and legacy key if needed.
