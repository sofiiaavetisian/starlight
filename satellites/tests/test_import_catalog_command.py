from unittest import mock

from django.core.management import call_command
from django.test import TestCase


class ImportCatalogCommandTests(TestCase):
    @mock.patch("satellites.management.commands.import_catalog.upsert_tles")
    @mock.patch("satellites.management.commands.import_catalog.parse_tle_catalog")
    @mock.patch("satellites.management.commands.import_catalog.httpx.Client")
    def test_import_catalog_downloads_and_upserts(self, mock_client_cls, mock_parse, mock_upsert):
        mock_client = mock.MagicMock()
        mock_response = mock.MagicMock()
        mock_response.text = "sample"
        mock_response.raise_for_status.return_value = None
        mock_client.get.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client_cls.return_value = mock_client

        mock_parse.return_value = [{"norad_id": 1, "name": "SAT", "line1": "L1", "line2": "L2"}]
        mock_upsert.return_value = 1

        call_command("import_catalog")

        mock_client.get.assert_called_once()
        mock_parse.assert_called_once_with("sample")
        mock_upsert.assert_called_once_with(mock_parse.return_value)
