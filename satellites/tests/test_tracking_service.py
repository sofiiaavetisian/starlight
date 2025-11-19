from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from satellites.models import Favorite, TLE
from satellites.services.tracking import (
    favorite_positions_for_user,
    satellite_detail_payload,
)


class TrackingServiceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="tracker", password="pass12345")
        self.tle = TLE.objects.create(
            norad_id=12345,
            name="Tracker Sat",
            line1="1 12345U 98067A   24172.00000000  .00016679  00000+0  29994-3 0  9994",
            line2="2 12345  51.6423  24.7205 0002520 156.6827  51.9026 15.50025038393561",
        )

    @mock.patch("satellites.services.tracking.propagate_now")
    @mock.patch("satellites.services.tracking.get_or_refresh_tle")
    def test_satellite_detail_payload_includes_label_and_stats(
        self, mock_get_or_refresh, mock_propagate
    ):
        mock_get_or_refresh.return_value = (
            "Tracker Sat",
            "line1",
            "line2",
        )
        mock_propagate.return_value = {"timestamp": "2024-01-01T00:00:00+00:00"}

        payload = satellite_detail_payload(self.tle)

        self.assertEqual(payload["satellite"]["label"], "Tracker Sat")
        self.assertIsNone(payload["error"])
        self.assertIn("timestamp_obj", payload["stats"])
        self.assertIsNotNone(payload["stats"]["timestamp_obj"])

    @mock.patch("satellites.services.tracking.propagate_now")
    @mock.patch("satellites.services.tracking.get_or_refresh_tle")
    def test_favorite_positions_for_user_filters_by_user(
        self, mock_get_or_refresh, mock_propagate
    ):
        other_user = get_user_model().objects.create_user(
            username="someone-else", password="pass12345"
        )
        Favorite.objects.create(user=self.user, norad_id=12345, name="Mine", notes="")
        Favorite.objects.create(user=other_user, norad_id=54321, name="Theirs", notes="")
        mock_get_or_refresh.return_value = ("Mine", "line1", "line2")
        mock_propagate.return_value = {"lat": 1.0, "lon": 2.0, "timestamp": "2024-01-01T00:00:00+00:00"}

        results = favorite_positions_for_user(self.user)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["norad_id"], 12345)
        self.assertEqual(results[0]["name"], "Mine")
