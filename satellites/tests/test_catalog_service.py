from django.test import TestCase

from satellites.models import TLE
from satellites.services.catalog import list_catalog_entries, search_catalog


class CatalogServiceTests(TestCase):
    def setUp(self):
        TLE.objects.create(
            norad_id=200,
            name="Beta Sat",
            line1="1 00000U 20000A   00000.00000000  .00000000  00000-0  00000-0 0  0000",
            line2="2 00000  98.0000  24.7205 0010000 156.0000  50.0000 14.00000000123456",
        )
        TLE.objects.create(
            norad_id=100,
            name="Alpha Sat",
            line1="1 10000U 20000A   00000.00000000  .00000000  00000-0  00000-0 0  0000",
            line2="2 10000  98.0000  24.7205 0010000 156.0000  50.0000 14.00000000123456",
        )

    def test_list_catalog_entries_returns_sorted_labels(self):
        entries = list_catalog_entries()
        labels = [item["label"] for item in entries]
        self.assertEqual(labels, ["Alpha Sat", "Beta Sat"])

    def test_search_catalog_handles_id_and_name(self):
        match = search_catalog("100")
        self.assertIsNotNone(match)
        self.assertEqual(match.norad_id, 100)

        match = search_catalog("beta sat")
        self.assertIsNotNone(match)
        self.assertEqual(match.norad_id, 200)

    def test_search_catalog_returns_none_for_empty_query(self):
        self.assertIsNone(search_catalog(""))
