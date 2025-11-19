from django.contrib.auth import get_user_model
from django.test import TestCase

from satellites.models import Favorite
from satellites.services.favorites import serialize_favorite, serialize_favorites


class FavoriteSerializationServiceTests(TestCase):
    """Unit tests for the favorite serialization helpers."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="serializer", password="pass12345")
        self.favorite = Favorite.objects.create(
            user=self.user,
            norad_id=999,
            name="Serializer Sat",
            notes="notes here",
        )

    def test_serialize_favorite_returns_expected_fields(self):
        data = serialize_favorite(self.favorite)
        self.assertEqual(
            data,
            {
                "id": self.favorite.id,
                "norad_id": 999,
                "name": "Serializer Sat",
                "notes": "notes here",
                "created_at": self.favorite.created_at.isoformat(),
            },
        )

    def test_serialize_favorites_handles_iterables(self):
        extra = Favorite.objects.create(
            user=self.user,
            norad_id=1000,
            name="Extra Sat",
            notes="",
        )
        data = serialize_favorites([self.favorite, extra])
        self.assertEqual(len(data), 2)
        self.assertEqual({fav["norad_id"] for fav in data}, {999, 1000})
