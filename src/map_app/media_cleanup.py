from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Iterable

from django.apps import apps
from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.management.base import CommandError
from django.db.models import FileField
from django.utils import timezone


@dataclass(frozen=True)
class CleanupCandidate:
    relpath: str
    fullpath: Path
    size_bytes: int


@dataclass(frozen=True)
class CleanupSummary:
    scanned_files: int
    target_files: int
    protected_files: int
    candidate_files: int
    candidate_size_bytes: int
    deleted_files: int
    deleted_size_bytes: int


def _normalize_prefix(prefix: str) -> str:
    normalized = (prefix or "").strip().lstrip("/")
    if normalized and not normalized.endswith("/"):
        normalized += "/"
    return normalized


def _media_root_path() -> Path:
    media_root = Path(settings.MEDIA_ROOT).resolve()
    if not media_root.exists() or not media_root.is_dir():
        raise CommandError(f"MEDIA_ROOT does not exist or is not a directory: {media_root}")
    return media_root


def _base_dir_path() -> Path:
    base_dir = getattr(settings, "BASE_DIR", None)
    if not base_dir:
        raise CommandError("BASE_DIR is not configured.")
    return Path(base_dir).resolve()


def _is_under(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _iter_target_files(media_root: Path, prefix: str) -> Iterable[Path]:
    for path in media_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(media_root).as_posix()
        if rel.startswith(prefix):
            yield path


def _collect_referenced_file_paths(prefix: str) -> set[str]:
    protected: set[str] = set()
    for model in apps.get_models():
        meta = model._meta
        if meta.abstract or meta.proxy:
            continue
        for field in meta.concrete_fields:
            if not isinstance(field, FileField):
                continue
            values = model._default_manager.exclude(**{field.name: ""}).values_list(field.name, flat=True).iterator()
            for name in values:
                if not name:
                    continue
                rel = str(name).strip().lstrip("/")
                if rel.startswith(prefix):
                    protected.add(rel)
    return protected


def _assert_delete_guardrails(*, force_local: bool) -> None:
    errors = []
    media_root = _media_root_path()
    base_dir = _base_dir_path()

    if not (bool(settings.DEBUG) or force_local):
        errors.append("Deletion requires DEBUG=True or --force-local.")
    if bool(getattr(settings, "USE_S3", False)):
        errors.append("Deletion is blocked when USE_S3=True.")
    if not isinstance(default_storage, FileSystemStorage):
        errors.append("Deletion requires local FileSystemStorage.")
    if not _is_under(media_root, base_dir):
        errors.append(f"Deletion requires MEDIA_ROOT under BASE_DIR. MEDIA_ROOT={media_root} BASE_DIR={base_dir}")

    if errors:
        raise CommandError(" ".join(errors))


def cleanup_local_media(*, prefix: str = "videos/", days: int | None = None, delete: bool = False, force_local: bool = False) -> CleanupSummary:
    normalized_prefix = _normalize_prefix(prefix) or "videos/"
    media_root = _media_root_path()
    protected = _collect_referenced_file_paths(normalized_prefix)

    cutoff_ts = None
    if days is not None:
        safe_days = max(0, int(days))
        cutoff_ts = (timezone.now() - timedelta(days=safe_days)).timestamp()

    scanned = 0
    target = 0
    protected_count = 0
    candidates: list[CleanupCandidate] = []
    for path in media_root.rglob("*"):
        if not path.is_file():
            continue
        scanned += 1
        rel = path.relative_to(media_root).as_posix()
        if not rel.startswith(normalized_prefix):
            continue
        target += 1
        if cutoff_ts is not None and path.stat().st_mtime >= cutoff_ts:
            continue
        if rel in protected:
            protected_count += 1
            continue
        size = path.stat().st_size
        candidates.append(CleanupCandidate(relpath=rel, fullpath=path, size_bytes=size))

    candidate_size = sum(item.size_bytes for item in candidates)

    deleted_files = 0
    deleted_size = 0
    if delete:
        _assert_delete_guardrails(force_local=force_local)
        for item in candidates:
            try:
                item.fullpath.unlink()
                deleted_files += 1
                deleted_size += item.size_bytes
            except FileNotFoundError:
                continue

    return CleanupSummary(
        scanned_files=scanned,
        target_files=target,
        protected_files=protected_count,
        candidate_files=len(candidates),
        candidate_size_bytes=candidate_size,
        deleted_files=deleted_files,
        deleted_size_bytes=deleted_size,
    )
