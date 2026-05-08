from unittest import TestCase
from unittest.mock import MagicMock, patch

from map_app.services.map_query_service import filter_locations_queryset


class MapQueryServiceTests(TestCase):
    @patch("map_app.services.map_query_service.get_location_model")
    @patch("map_app.services.map_query_service.normalize_selected_tags", return_value=["A", "B"])
    def test_filter_locations_queryset_resolves_location_model_for_tag_filter(
        self,
        _mock_normalize_selected_tags,
        mock_get_location_model,
    ):
        location_model = MagicMock()
        mock_get_location_model.return_value = location_model

        tag_match_qs = MagicMock()
        location_model.objects.filter.return_value = tag_match_qs
        tag_match_qs.annotate.return_value = tag_match_qs
        tag_match_qs.filter.return_value = tag_match_qs
        tag_match_qs.values.return_value = [{"id": 1}]

        location_qs = MagicMock()
        location_qs.filter.return_value = location_qs
        location_qs.distinct.return_value = location_qs

        result = filter_locations_queryset(location_qs, selected_tags=["A", "B"])

        mock_get_location_model.assert_called_once()
        location_model.objects.filter.assert_called_once()
        location_qs.filter.assert_called_once()
        self.assertIs(result, location_qs)
