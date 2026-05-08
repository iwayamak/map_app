from html import escape

import folium

from map_app.contracts.map_search_contract import MapSearchMarker
from map_app.map_page import build_marker_icon_html

NEW_VISIT_ICON_COLOR = "#ec4899"
REVISIT_ICON_COLOR = "#3b82f6"
UNVISITED_ICON_COLOR = "#eab308"


def resolve_icon_color(current_count):
    return NEW_VISIT_ICON_COLOR if current_count == 1 else REVISIT_ICON_COLOR


def serialize_performance_marker(performance, icon_color):
    location = performance.location
    return MapSearchMarker(
        performance_id=performance.id,
        location_id=location.id,
        location_name=location.name,
        date=performance.date.strftime("%Y/%m/%d"),
        lat=location.latitude,
        lng=location.longitude,
        icon_color=icon_color,
    )


def serialize_unvisited_marker(location):
    return MapSearchMarker(
        performance_id=0,
        location_id=location.id,
        location_name=location.name,
        date="未訪問",
        lat=location.latitude,
        lng=location.longitude,
        icon_color=UNVISITED_ICON_COLOR,
    )


def build_marker_tooltip(location_name, label):
    return f"{escape(location_name)} / {escape(label)}"


def add_performance_markers(marker_cluster, performances):
    running_visit_count = {}
    for perf in performances:
        location = perf.location
        running_visit_count[location.id] = running_visit_count.get(location.id, 0) + 1
        icon_color = resolve_icon_color(running_visit_count[location.id])
        marker = folium.Marker(
            [location.latitude, location.longitude],
            tooltip=build_marker_tooltip(location.name, f"{perf.date.year}/{perf.date.month}/{perf.date.day}"),
            icon=folium.DivIcon(html=build_marker_icon_html(icon_color)),
            **{"performanceId": perf.id, "locationId": location.id},
        )
        marker.add_to(marker_cluster)


def add_unvisited_markers(marker_cluster, locations):
    for location in locations:
        marker = folium.Marker(
            [location.latitude, location.longitude],
            tooltip=build_marker_tooltip(location.name, "未訪問"),
            icon=folium.DivIcon(html=build_marker_icon_html(UNVISITED_ICON_COLOR)),
            **{"performanceId": 0, "locationId": location.id},
        )
        marker.add_to(marker_cluster)
