from map_app.domain import get_default_domain_terms_func, get_tag_model
from django.conf import settings

LEGACY_NEW_TAG_NAME = "新規"


def _resolve_system_tag_names(domain_terms=None):
    defaults = get_default_domain_terms_func()()
    terms = defaults.copy()
    if isinstance(domain_terms, dict):
        for key, value in domain_terms.items():
            if isinstance(value, str) and value.strip():
                terms[key] = value.strip()
    info_only_key = getattr(settings, "MAP_APP_SYSTEM_INFO_ONLY_TAG_KEY", "system_info_only_tag_label")
    legacy_info_only_key = getattr(settings, "MAP_APP_SYSTEM_INFO_ONLY_TAG_LEGACY_KEY", "")
    unvisited_tag_name = terms["system_unvisited_tag_label"]
    primary_info_only = (terms.get(info_only_key) or "").strip()
    legacy_info_only = (terms.get(legacy_info_only_key) or "").strip() if legacy_info_only_key else ""
    # Backward compatibility: if the primary key still has the old default wording
    # but the legacy key has a customized value, prefer the customized legacy value.
    if primary_info_only and legacy_info_only and primary_info_only == "ピアノ情報のみ表示" and legacy_info_only != primary_info_only:
        domain_info_only_tag_name = legacy_info_only
    else:
        domain_info_only_tag_name = primary_info_only or legacy_info_only
    if not domain_info_only_tag_name:
        domain_info_only_tag_name = "情報のみ表示"
    return unvisited_tag_name, domain_info_only_tag_name


def _build_system_tag_styles(domain_terms=None):
    unvisited_tag_name, domain_info_only_tag_name = _resolve_system_tag_names(domain_terms)
    return (
        {"name": unvisited_tag_name, "color": "#fef3c7", "text_color": "#92400e"},
        {"name": domain_info_only_tag_name, "color": "#fce7f3", "text_color": "#9d174d"},
    )


def normalize_selected_tags(selected_tags, domain_terms=None):
    unvisited_tag_name, domain_info_only_tag_name = _resolve_system_tag_names(domain_terms)
    normalized = []
    for tag in (selected_tags or []):
        if not tag:
            continue
        if tag == LEGACY_NEW_TAG_NAME:
            tag = domain_info_only_tag_name
        normalized.append(tag)
    if "ピアノ情報のみ表示" in normalized and domain_info_only_tag_name not in normalized:
        normalized.append(domain_info_only_tag_name)
    if "未訪問" in normalized and unvisited_tag_name not in normalized:
        normalized.append(unvisited_tag_name)
    return list(dict.fromkeys(normalized))


def split_selected_tags(selected_tags, domain_terms=None):
    unvisited_tag_name, domain_info_only_tag_name = _resolve_system_tag_names(domain_terms)
    normalized_tags = normalize_selected_tags(selected_tags, domain_terms=domain_terms)
    system_tag_names = {unvisited_tag_name, domain_info_only_tag_name, LEGACY_NEW_TAG_NAME}
    actual_tags = [tag for tag in normalized_tags if tag not in system_tag_names]
    include_unvisited = unvisited_tag_name in normalized_tags
    include_domain_info_only = domain_info_only_tag_name in normalized_tags
    return actual_tags, include_unvisited, include_domain_info_only


def build_tag_context(selected_tags, domain_terms=None):
    Tag = get_tag_model()
    unvisited_tag_style, domain_info_only_tag_style = _build_system_tag_styles(domain_terms)
    tag_options = [
        {"name": tag.name, "color": tag.color, "text_color": tag.text_color}
        for tag in Tag.objects.order_by("order", "name").only("name", "color")
    ]
    tag_options.insert(0, domain_info_only_tag_style)
    tag_options.insert(0, unvisited_tag_style)
    tag_option_map = {tag["name"]: tag for tag in tag_options}
    selected_tag_items = [tag_option_map[name] for name in selected_tags if name in tag_option_map]
    return tag_options, selected_tag_items
