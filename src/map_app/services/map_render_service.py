import folium
from django.template.loader import render_to_string
from folium import Element
from folium.plugins import Fullscreen, LocateControl, MarkerCluster

from map_app.domain import template_name
from map_app.map_page import get_css_styles, get_javascript


def create_map():
    map_instance = folium.Map(
        location=[35.686, 138.360],
        zoom_start=5,
        tiles=None,
    )
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
        control=False,
        max_zoom=19,
        keep_buffer=4,
        update_when_idle=True,
        update_when_zooming=False,
    ).add_to(map_instance)
    Fullscreen().add_to(map_instance)
    LocateControl().add_to(map_instance)
    return map_instance


def create_marker_cluster():
    return MarkerCluster(
        options={
            "maxClusterRadius": 80,
            "spiderfyOnMaxZoom": True,
            "showCoverageOnHover": False,
            "zoomToBoundsOnClick": True,
            "spiderfyDistanceMultiplier": 1.5,
        }
    )


def render_summary_html(stats, domain_terms):
    return render_to_string(
        template_name("MAP_APP_TEMPLATE_SUMMARY_BOX", ""),
        {
            "total_locations": stats["total_locations"],
            "total_performances": stats["total_performances"],
            "tagged_locations": stats.get("tagged_locations", 0),
            "new_count": stats["new_count"],
            "revisit_count": stats["revisit_count"],
            "domain_terms": domain_terms,
        },
    )


def render_statistics_html(stats, domain_terms):
    statistics_payload = {
        "month_labels": stats["month_labels"],
        "month_values": stats["month_values"],
        "recent_visits": stats["recent_visits_data"],
        "top_locations": stats["top_locations_data"],
    }
    return render_to_string(
        template_name("MAP_APP_TEMPLATE_STATISTICS", ""),
        {
            "statistics_payload": statistics_payload,
            "recent_visits": stats["recent_visits_data"],
            "top_locations": stats["top_locations_data"],
            "domain_terms": domain_terms,
        },
    )


def render_header_html(user, site_settings, search_query, selected_tags, selected_tag_items, tag_options):
    return render_to_string(
        template_name("MAP_APP_TEMPLATE_HEADER", ""),
        {
            "user": user,
            "site_settings": site_settings,
            "domain_terms": site_settings.get_domain_terms(),
            "search_query": search_query,
            "selected_tags": selected_tags,
            "selected_tag_items": selected_tag_items,
            "tag_options": tag_options,
        },
    )


def render_hamburger_menu_html(user, domain_terms):
    return render_to_string(
        template_name("MAP_APP_TEMPLATE_HAMBURGER_MENU", ""),
        {
            "user": user,
            "domain_terms": domain_terms,
        },
    )


def render_modals_html(domain_terms):
    return render_to_string(
        template_name("MAP_APP_TEMPLATE_MODALS", ""),
        {"domain_terms": domain_terms},
    )


def attach_page_elements(
    map_instance,
    site_settings,
    header_html,
    hamburger_menu_html,
    summary_html,
    statistics_html,
    modals_html,
):
    map_instance.get_root().header.add_child(Element(build_page_title(site_settings)))
    map_instance.get_root().header.add_child(Element(get_css_styles(site_settings)))
    map_instance.get_root().header.add_child(Element(get_javascript(map_instance._id)))
    map_instance.get_root().html.add_child(Element(header_html))
    map_instance.get_root().html.add_child(Element(hamburger_menu_html))
    map_instance.get_root().html.add_child(Element(summary_html))
    map_instance.get_root().html.add_child(Element(statistics_html))
    map_instance.get_root().html.add_child(Element(modals_html))


def build_page_title(site_settings):
    terms = site_settings.get_domain_terms()
    if site_settings.site_title:
        return f"<title>{site_settings.site_title}</title>"
    return f"<title>{terms.get('app_title', 'ストリートピアノマップ')}</title>"
