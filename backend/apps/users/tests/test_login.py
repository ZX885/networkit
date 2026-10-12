from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.profiles.tests.factories import make_user

from .helpers import OWN_KEYS, PASSWORD, error_of, make_account

LOGIN = "/api/auth/login/"
LOGOUT = "/api/auth/logout/"


class LoginTests(APITestCase):
    def login(self, email="user@example.com", password=PASSWORD):
        return self.client.post(LOGIN, {"email": email, "password": password}, format="json")

    def test_success_returns_own_profile_and_creates_session(self):
        make_account()

        response = self.login()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), OWN_KEYS)
        self.assertEqual(response.json()["email"], "user@example.com")
        self.assertIn("sessionid", response.cookies)
        self.assertEqual(self.client.get("/api/me/").status_code, 200)

    def test_email_case_does_not_matter(self):
        make_account()

        self.assertEqual(self.login(email="USER@Example.com").status_code, 200)

    def test_session_key_is_replaced_on_login(self):
        make_account()
        session = self.client.session
        session["anonymous"] = True
        session.save()
        old_key = self.client.session.session_key

        self.login()

        self.assertNotEqual(self.client.session.session_key, old_key)

    def test_wrong_password_and_unknown_email_look_the_same(self):
        make_account()

        wrong_password = self.login(password="wrong-password-1")
        unknown_email = self.login(email="nobody@example.com")

        self.assertEqual(wrong_password.status_code, 400)
        self.assertEqual(error_of(wrong_password)["code"], "invalid_credentials")
        self.assertEqual(wrong_password.json(), unknown_email.json())

    def test_unverified_email_is_reported_only_with_the_right_password(self):
        make_account(verified=False)

        right = self.login()
        wrong = self.login(password="wrong-password-1")

        self.assertEqual(right.status_code, 403)
        self.assertEqual(error_of(right)["code"], "email_not_verified")
        self.assertEqual(error_of(wrong)["code"], "invalid_credentials")
        self.assertNotIn("sessionid", right.cookies)

    def test_banned_user_is_reported_only_with_the_right_password(self):
        user = make_account()
        user.is_banned = True
        user.save()

        right = self.login()
        wrong = self.login(password="wrong-password-1")

        self.assertEqual(right.status_code, 403)
        self.assertEqual(error_of(right)["code"], "account_banned")
        self.assertEqual(error_of(wrong)["code"], "invalid_credentials")

    def test_inactive_account_cannot_log_in(self):
        user = make_account()
        user.is_active = False
        user.save()

        self.assertEqual(error_of(self.login())["code"], "invalid_credentials")

    def test_already_signed_in(self):
        user = make_account()
        self.client.force_login(user)

        response = self.login()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(error_of(response)["code"], "already_authenticated")

    def test_account_without_profile_cannot_sign_in_through_api(self):
        make_user(email="staff@example.com", password=PASSWORD, email_verified_at=timezone.now())

        response = self.login(email="staff@example.com")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(error_of(response)["code"], "permission_denied")

    def test_validation_errors(self):
        response = self.client.post(LOGIN, {"email": "not-an-email"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_of(response)["code"], "validation_error")


@override_settings(THROTTLING_ENABLED=True)
class LoginThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_sixth_wrong_attempt_in_a_minute_is_throttled(self):
        make_account()
        for _ in range(5):
            response = self.client.post(LOGIN, {"email": "user@example.com", "password": "wrong-pass-1"}, format="json")
            self.assertEqual(response.status_code, 400)

        response = self.client.post(LOGIN, {"email": "user@example.com", "password": "wrong-pass-1"}, format="json")

        self.assertEqual(response.status_code, 429)
        error = error_of(response)
        self.assertEqual(error["code"], "throttled")
        self.assertIsInstance(error["retry_after"], int)
        self.assertGreater(error["retry_after"], 0)
        self.assertEqual(response["Retry-After"], str(error["retry_after"]))
        self.assertEqual(set(error), {"code", "message", "retry_after"})


class LogoutTests(APITestCase):
    def test_logout_ends_the_session(self):
        make_account()
        self.client.post(LOGIN, {"email": "user@example.com", "password": PASSWORD}, format="json")
        self.assertEqual(self.client.get("/api/me/").status_code, 200)

        response = self.client.post(LOGOUT)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get("/api/me/").status_code, 401)

    def test_logout_requires_login(self):
        response = APIClient().post(LOGOUT)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(error_of(response)["code"], "not_authenticated")
