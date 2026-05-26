from map_app.contracts.map_search_contract import (
    MapSearchRecentVisit,
    MapSearchStatistics,
    MapSearchSummary,
    MapSearchTopLocation,
)


def serialize_map_summary(stats, markers, unvisited_locations):
    tagged_locations = stats.get("tagged_locations", 0)
    return MapSearchSummary(
        total_locations=stats["total_locations"] + len(unvisited_locations),
        total_activity_logs=stats["total_activity_logs"],
        marker_count=len(markers),
        tagged_locations=tagged_locations,
        new_count=stats["new_count"],
        revisit_count=stats["revisit_count"],
    )


def serialize_map_statistics(stats):
    return MapSearchStatistics(
        month_labels=list(stats["month_labels"]),
        month_values=list(stats["month_values"]),
        recent_visits=[
            MapSearchRecentVisit(
                location_name=item["location_name"],
                date=item["date"],
                title=item["title"],
                latitude=item["latitude"],
                longitude=item["longitude"],
            )
            for item in stats["recent_visits_data"]
        ],
        top_locations=[
            MapSearchTopLocation(
                name=item["name"],
                count=item["count"],
                latitude=item["latitude"],
                longitude=item["longitude"],
            )
            for item in stats["top_locations_data"]
        ],
    )
