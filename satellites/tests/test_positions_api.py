from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from satellites.models import Favorite


class PositionsBatchAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="positions", password="pass12345")
        Favorite.objects.create(user=self.user, norad_id=444, name="Fav", notes="")

    def test_positions_batch_requires_auth(self):
        response = self.client.get(reverse("positions-batch"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch("satellites.services.tracking.propagate_now")
    @mock.patch("satellites.services.tracking.get_or_refresh_tle")
    def test_positions_batch_returns_user_positions(
        self, mock_get_or_refresh, mock_propagate
    ):
        mock_get_or_refresh.return_value = ("Fav", "line1", "line2")
        mock_propagate.return_value = {"lat": 1.0, "lon": 2.0, "timestamp": "2024-01-01T00:00:00+00:00"}

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("positions-batch"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["norad_id"], 444)
