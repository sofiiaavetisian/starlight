import math
from datetime import datetime, timezone
from unittest import mock

from django.test import SimpleTestCase

from satellites.services import propagation


class PropagationServiceTests(SimpleTestCase):
    def test_gmst_from_jd_matches_known_value(self):
        gmst = propagation._gmst_from_jd(2451545.0)
        expected = math.radians(100.46061837)
        self.assertAlmostEqual(gmst, expected, places=6)

    @mock.patch("satellites.services.propagation._ecef_to_geodetic")
    @mock.patch("satellites.services.propagation.Satrec")
    def test_propagate_now_allows_injected_timestamp(
        self, mock_satrec, mock_transform
    ):
        mock_sat = mock.Mock()
        mock_sat.sgp4.return_value = (
            0,
            (7000.0, 0.0, 0.0),
            (0.0, 7.5, 0.0),
        )
        mock_satrec.twoline2rv.return_value = mock_sat
        mock_transform.transform.return_value = (10.0, 20.0, 400000.0)

        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        data = propagation.propagate_now("line1", "line2", timestamp=ts)

        self.assertEqual(data["timestamp"], ts.isoformat())
        self.assertAlmostEqual(data["alt_km"], 400.0)
        mock_sat.sgp4.assert_called_once()
