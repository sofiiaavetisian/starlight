from datetime import datetime, timedelta, timezone
from unittest import mock

from django.test import TestCase

from satellites.models import TLE
from satellites.services import tle_fetcher


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


class FakeClient:
    def __init__(self, text: str):
        self._response = FakeResponse(text)
        self.requested_url = None
        self.closed = False

    def get(self, url: str):
        self.requested_url = url
        return self._response

    def close(self):
        self.closed = True


class TLEFetcherTests(TestCase):
    def setUp(self):
        self.sample_text = "\n".join(
            [
                "SAT A",
                "1 12345U 20000A   00000.00000000  .00000000  00000-0  00000-0 0  0000",
                "2 12345  98.0000  24.7205 0010000 156.0000  50.0000 14.00000000123456",
            ]
        )

    def test_parse_tle_catalog_returns_records(self):
        records = tle_fetcher.parse_tle_catalog(self.sample_text)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["norad_id"], 12345)

    def test_fetch_tle_uses_injected_client(self):
        client = FakeClient(self.sample_text)
        name, line1, line2 = tle_fetcher.fetch_tle_from_celestrak(12345, client=client)
        self.assertEqual(name, "SAT A")
        self.assertTrue(client.closed is False)
        self.assertIn("CATNR=12345", client.requested_url)

    def test_get_or_refresh_tle_uses_cache_when_recent(self):
        tle = TLE.objects.create(
            norad_id=12345, name="Old", line1="L1", line2="L2"
        )
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        name, line1, line2 = tle_fetcher.get_or_refresh_tle(
            12345, max_age_hours=48, now=now
        )
        self.assertEqual((name, line1, line2), ("Old", "L1", "L2"))

    def test_get_or_refresh_tle_fetches_when_stale(self):
        tle = TLE.objects.create(
            norad_id=12345, name="Old", line1="L1", line2="L2"
        )
        stale_time = datetime(2023, 1, 1, tzinfo=timezone.utc)
        TLE.objects.filter(pk=tle.pk).update(updated_at=stale_time)

        client = FakeClient(self.sample_text)
        now = stale_time + timedelta(days=3)
        name, line1, line2 = tle_fetcher.get_or_refresh_tle(
            12345, max_age_hours=24, now=now, client=client
        )
        self.assertEqual(name, "SAT A")
        tle.refresh_from_db()
        self.assertEqual(tle.name, "SAT A")
