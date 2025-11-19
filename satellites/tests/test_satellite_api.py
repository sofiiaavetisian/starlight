from unittest import mock

from django.test import TestCase
from django.urls import reverse

from satellites.models import TLE


class SatelliteAPITests(TestCase):
    def setUp(self):
        self.tle = TLE.objects.create(
            norad_id=555,
            name="API Sat",
            line1="1 00555U 20000A   00000.00000000  .00000000  00000-0  00000-0 0  0000",
            line2="2 00555  98.0000  24.7205 0010000 156.0000  50.0000 14.00000000123456",
        )

    def test_satellite_list_endpoint_returns_catalog(self):
        response = self.client.get(reverse("satellites-list"))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["norad_id"], self.tle.norad_id)

    @mock.patch("satellites.views.satellite_position_payload")
    def test_position_single_returns_payload(self, mock_payload):
        mock_payload.return_value = {
            "norad_id": self.tle.norad_id,
            "name": "API Sat",
            "lat": 1.0,
            "lon": 2.0,
            "alt_km": 400.0,
            "vel_kms": 7.5,
            "timestamp": "2024-01-01T00:00:00+00:00",
        }
        response = self.client.get(
            reverse("position-single", args=[self.tle.norad_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["norad_id"], self.tle.norad_id)
        mock_payload.assert_called_once_with(self.tle.norad_id)
