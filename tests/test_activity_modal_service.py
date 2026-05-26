from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

from map_app.services.activity_modal_service import _build_common_modal_payload


class ActivityModalServiceTests(TestCase):
    @patch("map_app.services.activity_modal_service.build_link_preview_map", return_value={})
    @patch("map_app.services.activity_modal_service._build_custom_fields_payload", return_value=[])
    @patch("map_app.services.activity_modal_service.get_domain_field_definition_model")
    def test_build_common_modal_payload_resolves_domain_field_definition(
        self,
        mock_get_domain_field_definition_model,
        _mock_custom_fields,
        _mock_link_preview,
    ):
        mock_get_domain_field_definition_model.return_value = SimpleNamespace(TARGET_LOCATION="location")
        location = SimpleNamespace(
            name="Test",
            nearest_station="Station",
            walking_minutes=3,
            playable_schedule_note="note",
            detail_note="",
            custom_data={},
            image=None,
            photos=MagicMock(),
            tags=MagicMock(),
        )
        location.photos.only.return_value.order_by.return_value = []
        location.tags.only.return_value.order_by.return_value = []

        payload = _build_common_modal_payload(
            record_id=1,
            location=location,
            date=SimpleNamespace(strftime=lambda _fmt: "2026年05月08日"),
            current_count=1,
            activity_items=[],
        )

        self.assertEqual(payload["id"], 1)
        mock_get_domain_field_definition_model.assert_called_once()
