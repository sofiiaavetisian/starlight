from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from satellites.models import TLE

class HomePageTests(TestCase):
    def test_homepage_renders(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Track satellites beautifully")

class CatalogTests(TestCase):
    def setUp(self):
        TLE.objects.create(
            norad_id=25544,
            name="ISS (ZARYA)",
            line1="1 25544U 98067A   24172.54827691  .00016679  00000+0  29994-3 0  9994",
            line2="2 25544  51.6423  24.7205 0002520 156.6827  51.9026 15.50025038393561",
        )

    def test_catalog_renders_and_includes_satellite(self):
        response = self.client.get(reverse("catalog"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Satellite catalog")
        self.assertContains(response, "ISS (ZARYA)")

class FavoritesTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="tester", password="secret123")
        TLE.objects.create(
            norad_id=40000,
            name="TEST SAT",
            line1="1 40000U 14001A   24172.54827691  .00000000  00000+0  00000-0 0  9995",
            line2="2 40000  98.0000  24.7205 0010000 156.0000  50.0000 14.00000000123456",
        )

    def test_favorites_requires_login(self):
        response = self.client.get(reverse("favorites"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('favorites')}")

    def test_add_favorite_flow(self):
        self.client.login(username="tester", password="secret123")
        response = self.client.post(reverse("favorite-add", args=[40000]))
        self.assertEqual(response.status_code, 302)

        favorites_page = self.client.get(reverse("favorites"))
        self.assertEqual(favorites_page.status_code, 200)
        self.assertContains(favorites_page, "TEST SAT")
