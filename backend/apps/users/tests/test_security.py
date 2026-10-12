from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import Client
from rest_framework.test import APIClient, APITestCase

from apps.users.models import User

from .helpers import PASSWORD, error_of, make_account, registration_payload


class CsrfTests(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf_token(self):
        response = self.client.get("/api/auth/csrf/")
        self.assertEqual(response.status_code, 204)
        return response.cookies["csrftoken"].value

    def test_csrf_endpoint_sets_cookie_readable_by_js(self):
        response = self.client.get("/api/auth/csrf/")

        self.assertEqual(response.status_code, 204)
        cookie = response.cookies["csrftoken"]
        self.assertEqual(cookie["httponly"], "")  # JS должен читать значение
        self.assertEqual(cookie["samesite"], "Lax")

    def test_anonymous_post_without_token_is_rejected(self):
        for url, body in [
            ("/api/auth/register/", registration_payload()),
            ("/api/auth/login/", {"email": "a@example.com", "password": "x"}),
            ("/api/auth/verify-email/", {"token": "x"}),
        ]:
            with self.subTest(url=url):
                response = self.client.post(url, body, format="json")
                self.assertEqual(response.status_code, 403)
                self.assertEqual(error_of(response)["code"], "csrf_failed")

    def test_anonymous_post_with_token_passes(self):
        token = self.csrf_token()

        response = self.client.post(
            "/api/auth/register/", registration_payload(), format="json", headers={"X-CSRFToken": token}
        )

        self.assertEqual(response.status_code, 201)

    def test_authenticated_unsafe_requests_need_token(self):
        user = make_account()
        self.client.force_login(user)
        token = self.csrf_token()

        without = self.client.patch("/api/me/", {"city": "Samarkand"}, format="json")
        with_token = self.client.patch(
            "/api/me/", {"city": "Samarkand"}, format="json", headers={"X-CSRFToken": token}
        )

        self.assertEqual(without.status_code, 403)
        self.assertEqual(error_of(without)["code"], "csrf_failed")
        self.assertEqual(with_token.status_code, 200)

    def test_safe_requests_do_not_need_token(self):
        self.assertEqual(self.client.get("/api/health/").status_code, 200)

    def test_login_with_token_issues_a_new_csrf_token(self):
        make_account()
        token = self.csrf_token()

        response = self.client.post(
            "/api/auth/login/",
            {"email": "user@example.com", "password": PASSWORD},
            format="json",
            headers={"X-CSRFToken": token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)  # после входа токен обновляется


class CookieSettingsTests(APITestCase):
    def test_session_cookie_flags(self):
        make_account()

        response = self.client.post(
            "/api/auth/login/", {"email": "user@example.com", "password": PASSWORD}, format="json"
        )

        cookie = response.cookies["sessionid"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(settings.SESSION_COOKIE_AGE, 14 * 24 * 60 * 60)
        self.assertFalse(settings.SESSION_SAVE_EVERY_REQUEST)  # срок не продлевается
        self.assertFalse(settings.CSRF_COOKIE_HTTPONLY)


class BannedUserTests(APITestCase):
    def test_banned_user_with_live_session_is_rejected(self):
        user = make_account()
        self.client.force_login(user)
        User.objects.filter(pk=user.pk).update(is_banned=True)

        for method, url in [("get", "/api/me/"), ("post", "/api/auth/logout/")]:
            with self.subTest(url=url):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(error_of(response)["code"], "account_banned")

    def test_admin_ban_action_ends_sessions(self):
        victim = make_account(email="victim@example.com", username="victim")
        other = make_account(email="other@example.com", username="other")
        victim_client, other_client = APIClient(), APIClient()
        victim_client.force_login(victim)
        other_client.force_login(other)
        admin = User.objects.create_superuser(email="admin@example.com", password=PASSWORD)
        admin_client = Client()
        admin_client.force_login(admin)

        response = admin_client.post(
            "/admin/users/user/", {"action": "ban_users", "_selected_action": [victim.pk]}
        )

        self.assertEqual(response.status_code, 302)
        victim.refresh_from_db()
        self.assertTrue(victim.is_banned)
        self.assertIsNotNone(victim.banned_at)
        self.assertEqual(victim_client.get("/api/me/").status_code, 401)  # сессии больше нет
        self.assertEqual(other_client.get("/api/me/").status_code, 200)  # чужая сессия цела
        self.assertEqual(Session.objects.count(), 2)  # сессии админа и второго пользователя
