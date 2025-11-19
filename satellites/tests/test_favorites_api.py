from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from satellites.models import Favorite


class FavoriteAPITests(APITestCase):
    """Integration tests for the favorites API endpoints."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="apiuser", password="pass12345")
        self.other_user = User.objects.create_user(username="other", password="pass12345")

    def test_list_requires_authentication(self):
        response = self.client.get(reverse("favorite-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_only_sees_their_own_favorites(self):
        Favorite.objects.create(user=self.user, norad_id=111, name="Mine", notes="")
        Favorite.objects.create(user=self.other_user, norad_id=222, name="Not mine", notes="")

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("favorite-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["norad_id"], 111)
        self.assertEqual(response.data[0]["name"], "Mine")

    def test_create_favorite_assigns_request_user(self):
        self.client.force_authenticate(user=self.user)
        payload = {"norad_id": 333, "name": "API Sat", "notes": "from api"}

        response = self.client.post(reverse("favorite-list"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Favorite.objects.get(pk=response.data["id"])
        self.assertEqual(created.user, self.user)
        self.assertEqual(created.norad_id, 333)
