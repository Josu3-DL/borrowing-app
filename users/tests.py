from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AuthenticationTests(TestCase):
    def setUp(self):
        self.password = "UnaClaveSegura2026!"
        self.user = User.objects.create_user(
            username="ana",
            email="ana@example.com",
            password=self.password,
            first_name="Ana",
        )

    def test_registration_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "username": "luis",
                "first_name": "Luis",
                "last_name": "Pérez",
                "email": "LUIS@example.com",
                "phone": "8888-8888",
                "password1": "OtraClaveSegura2026!",
                "password2": "OtraClaveSegura2026!",
            },
        )

        self.assertRedirects(response, reverse("users:profile"))
        self.assertTrue(User.objects.filter(username="luis").exists())
        self.assertEqual(
            str(self.client.session["_auth_user_id"]),
            str(User.objects.get(username="luis").pk),
        )

    def test_registration_rejects_duplicate_email_ignoring_case(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "username": "otra-persona",
                "first_name": "Otra",
                "last_name": "Persona",
                "email": "ANA@EXAMPLE.COM",
                "password1": "OtraClaveSegura2026!",
                "password2": "OtraClaveSegura2026!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe una cuenta")
        self.assertEqual(User.objects.count(), 1)

    def test_registration_rejects_duplicate_username(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "username": "ana",
                "first_name": "Otra",
                "last_name": "Persona",
                "email": "otra@example.com",
                "password1": "OtraClaveSegura2026!",
                "password2": "OtraClaveSegura2026!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe un usuario con este nombre")
        self.assertEqual(User.objects.count(), 1)

    def test_login_with_username(self):
        response = self.client.post(
            reverse("users:login"),
            {"username": self.user.username, "password": self.password},
        )

        self.assertRedirects(response, reverse("users:profile"))

    def test_email_cannot_be_used_to_log_in(self):
        response = self.client.post(
            reverse("users:login"),
            {"username": self.user.email, "password": self.password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_invalid_login_does_not_authenticate(self):
        response = self.client.post(
            reverse("users:login"),
            {"username": self.user.username, "password": "incorrecta"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("users:profile"))

        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next={reverse('users:profile')}",
        )

    def test_authenticated_user_can_update_own_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:profile"),
            {
                "username": "ana-maria",
                "first_name": "Ana María",
                "last_name": "López",
                "email": "nuevo@example.com",
                "phone": "7777-7777",
            },
        )

        self.assertRedirects(response, reverse("users:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "ana-maria")
        self.assertEqual(self.user.first_name, "Ana María")
        self.assertEqual(self.user.email, "nuevo@example.com")

    def test_profile_rejects_another_users_email_ignoring_case(self):
        User.objects.create_user(
            username="otra",
            email="otra@example.com",
            password="OtraClaveSegura2026!",
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("users:profile"),
            {
                "username": "ana",
                "first_name": "Ana",
                "last_name": "",
                "email": "OTRA@EXAMPLE.COM",
                "phone": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe una cuenta")
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "ana@example.com")

    def test_database_rejects_case_insensitive_duplicate_email(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create(username="otra", email="ANA@EXAMPLE.COM")

    def test_logout_accepts_post_and_ends_session(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("users:logout"))

        self.assertRedirects(response, reverse("users:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_rejects_get(self):
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(reverse("users:logout")).status_code, 405)
