from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MapSearchSummary:
    total_locations: int
    total_activity_logs: int
    total_performances: int
    marker_count: int
    tagged_locations: int
    new_count: int
    revisit_count: int


@dataclass(frozen=True)
class MapSearchMarker:
    activity_log_id: int
    performance_id: int
    location_id: int
    location_name: str
    date: str
    lat: float
    lng: float
    icon_color: str


@dataclass(frozen=True)
class MapSearchRecentVisit:
    location_name: str
    date: str
    title: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class MapSearchTopLocation:
    name: str
    count: int
    latitude: float
    longitude: float


@dataclass(frozen=True)
class MapSearchStatistics:
    month_labels: list[str]
    month_values: list[int]
    recent_visits: list[MapSearchRecentVisit]
    top_locations: list[MapSearchTopLocation]


@dataclass(frozen=True)
class MapSearchPayload:
    markers: list[MapSearchMarker]
    summary: MapSearchSummary
    statistics: MapSearchStatistics

    def to_dict(self) -> dict[str, Any]:
        return {
            "markers": [asdict(marker) for marker in self.markers],
            "summary": asdict(self.summary),
            "statistics": asdict(self.statistics),
        }


MAP_SEARCH_SUMMARY_FIELDS = tuple(MapSearchSummary.__dataclass_fields__.keys())
MAP_SEARCH_MARKER_FIELDS = tuple(MapSearchMarker.__dataclass_fields__.keys())
MAP_SEARCH_STATISTICS_FIELDS = tuple(MapSearchStatistics.__dataclass_fields__.keys())
MAP_SEARCH_RECENT_VISIT_FIELDS = tuple(MapSearchRecentVisit.__dataclass_fields__.keys())
MAP_SEARCH_TOP_LOCATION_FIELDS = tuple(MapSearchTopLocation.__dataclass_fields__.keys())

MAP_SEARCH_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["markers", "summary", "statistics"],
    "additionalProperties": False,
    "properties": {
        "markers": {
            "type": "array",
            "items": {
                "type": "object",
                "required": list(MAP_SEARCH_MARKER_FIELDS),
                "additionalProperties": False,
                "properties": {
                    "activity_log_id": {"type": "integer"},
                    "performance_id": {"type": "integer"},
                    "location_id": {"type": "integer"},
                    "location_name": {"type": "string"},
                    "date": {"type": "string"},
                    "lat": {"type": "number"},
                    "lng": {"type": "number"},
                    "icon_color": {"type": "string"},
                },
            },
        },
        "summary": {
            "type": "object",
            "required": list(MAP_SEARCH_SUMMARY_FIELDS),
            "additionalProperties": False,
                "properties": {
                    "total_locations": {"type": "integer"},
                    "total_activity_logs": {"type": "integer"},
                    "total_performances": {"type": "integer"},
                "marker_count": {"type": "integer"},
                "tagged_locations": {"type": "integer"},
                "new_count": {"type": "integer"},
                "revisit_count": {"type": "integer"},
            },
        },
        "statistics": {
            "type": "object",
            "required": list(MAP_SEARCH_STATISTICS_FIELDS),
            "additionalProperties": False,
            "properties": {
                "month_labels": {"type": "array", "items": {"type": "string"}},
                "month_values": {"type": "array", "items": {"type": "integer"}},
                "recent_visits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": list(MAP_SEARCH_RECENT_VISIT_FIELDS),
                        "additionalProperties": False,
                        "properties": {
                            "location_name": {"type": "string"},
                            "date": {"type": "string"},
                            "title": {"type": "string"},
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"},
                        },
                    },
                },
                "top_locations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": list(MAP_SEARCH_TOP_LOCATION_FIELDS),
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "count": {"type": "integer"},
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"},
                        },
                    },
                },
            },
        },
    },
}


def validate_map_search_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Map search payload must be a JSON object.")
