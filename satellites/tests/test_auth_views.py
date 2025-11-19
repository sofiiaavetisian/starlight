from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthViewsTests(TestCase):
    def test_signup_page_renders(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create account")

    def test_signup_creates_user_and_redirects(self):
        payload = {
            "username": "student1",
            "password1": "strong-pass-123",
            "password2": "strong-pass-123",
        }
        response = self.client.post(reverse("signup"), payload)
        self.assertRedirects(response, reverse("login"))
        User = get_user_model()
        self.assertTrue(User.objects.filter(username="student1").exists())
