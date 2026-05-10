# Changelog

## 0.1.2 - 2026-05-10

- Added abstract base models for shared schema reuse in host Django apps.
- Added shared site-context loader and switched map page services to it.
- Added dependency-injection points to video processing services (`ffmpeg`, `metadata`, `thumbnail`, `transcode`, `pipeline`).
- Added dependency-injection points to `healthcheck`, `link_preview`, and `performance_modal` services.
- Added regression tests for injection paths and base models.

## 0.1.1 - 2026-05-08

- Fixed `NameError` in modal payload builder by resolving `DomainFieldDefinition` in `_build_common_modal_payload`.
- Fixed `NameError` in location filtering by resolving `Location` model in `filter_locations_queryset`.
- Added package-level regression tests for the two issues above.
- Added migration checklist document for host apps.

## 0.1.0

- Initial extraction of reusable map services, contracts, and rendering helpers.
