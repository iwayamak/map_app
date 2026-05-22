from django.conf import settings

from map_app.contracts.map_search_contract import (
    MapSearchPayload,
)
from map_app.domain import get_statistics_builder
from map_app.services.map_marker_service import (
    add_performance_markers,
    add_unvisited_markers,
    resolve_icon_color,
    serialize_performance_marker,
    serialize_unvisited_marker,
)
from map_app.services.map_query_service import (
    get_filtered_performance_queryset,
    get_filtered_unvisited_location_queryset,
)
from map_app.services.map_render_service import (
    attach_page_elements,
    create_map,
    create_marker_cluster,
    render_hamburger_menu_html,
    render_header_html,
    render_modals_html,
    render_statistics_html,
    render_summary_html,
)
from map_app.services.map_summary_service import serialize_map_statistics, serialize_map_summary
from map_app.services.map_tag_service import build_tag_context, normalize_selected_tags
from map_app.services.site_context_service import load_site_context


def build_map_search_payload(search_query="", selected_tags=None):
    build_map_statistics = get_statistics_builder()
    search_query = (search_query or "").strip()
    site_settings, domain_terms = load_site_context()
    selected_tags = normalize_selected_tags(selected_tags, domain_terms=domain_terms)

    performances = list(
        get_filtered_performance_queryset(
            search_query=search_query,
            selected_tags=selected_tags,
            domain_terms=domain_terms,
        )
    )
    unvisited_locations = list(
        get_filtered_unvisited_location_queryset(
            search_query=search_query,
            selected_tags=selected_tags,
            domain_terms=domain_terms,
        )
    )
    stats = build_map_statistics(performances)

    running_visit_count = {}
    markers = []
    for perf in performances:
        location = perf.location
        running_visit_count[location.id] = running_visit_count.get(location.id, 0) + 1
        icon_color = resolve_icon_color(running_visit_count[location.id])
        markers.append(serialize_performance_marker(perf, icon_color))
    for location in unvisited_locations:
        markers.append(serialize_unvisited_marker(location))

    payload = MapSearchPayload(
        markers=markers,
        summary=serialize_map_summary(stats, markers, unvisited_locations),
        statistics=serialize_map_statistics(stats),
    )
    return payload.to_dict()


def render_map_page_html(user, search_query="", selected_tags=None):
    build_map_statistics = get_statistics_builder()
    search_query = (search_query or "").strip()
    site_settings, domain_terms = load_site_context()
    selected_tags = normalize_selected_tags(selected_tags, domain_terms=domain_terms)

    map_instance = create_map()
    marker_cluster = create_marker_cluster()

    defer_initial_map_data = (
        bool(getattr(settings, "MAP_APP_DEFER_INITIAL_MAP_DATA", False))
        and not search_query
        and not selected_tags
    )
    if defer_initial_map_data:
        all_performances = []
        unvisited_locations = []
    else:
        all_performances = list(
            get_filtered_performance_queryset(
                search_query=search_query,
                selected_tags=selected_tags,
                domain_terms=domain_terms,
            )
        )
        unvisited_locations = list(
            get_filtered_unvisited_location_queryset(
                search_query=search_query,
                selected_tags=selected_tags,
                domain_terms=domain_terms,
            )
        )

    stats = build_map_statistics(all_performances)
    stats["total_locations"] = stats["total_locations"] + len(unvisited_locations)
    stats["marker_count"] = len(all_performances) + len(unvisited_locations)
    tag_options, selected_tag_items = build_tag_context(selected_tags, domain_terms=domain_terms)
    add_performance_markers(marker_cluster, all_performances)
    add_unvisited_markers(marker_cluster, unvisited_locations)

    marker_cluster.add_to(map_instance)

    summary_html = render_summary_html(stats, domain_terms)
    statistics_html = render_statistics_html(stats, domain_terms)
    modals_html = render_modals_html(domain_terms)
    header_html = render_header_html(
        user=user,
        site_settings=site_settings,
        search_query=search_query,
        selected_tags=selected_tags,
        selected_tag_items=selected_tag_items,
        tag_options=tag_options,
    )
    hamburger_menu_html = render_hamburger_menu_html(user, domain_terms)
    attach_page_elements(
        map_instance,
        site_settings,
        header_html,
        hamburger_menu_html,
        summary_html,
        statistics_html,
        modals_html,
    )

    return {
        "html": map_instance.get_root().render(),
        "performance_count": len(all_performances),
        "search_query": search_query,
        "selected_tags": selected_tags,
    }
