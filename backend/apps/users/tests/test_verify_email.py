import time
from unittest import mock

from django.core import mail, signing
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.users.tokens import MAX_AGE_SECONDS

from .helpers import error_of, make_account, registration_payload, token_from_last_email

VERIFY = "/api/auth/verify-email/"
RESEND = "/api/auth/resend-verification/"


class VerifyEmailTests(APITestCase):
    def setUp(self):
        self.client.post("/api/auth/register/", registration_payload(), format="json")
        self.token = token_from_last_email()
        self.user = User.objects.get(email="jane@example.com")

    def verify(self, token):
        return self.client.post(VERIFY, {"token": token}, format="json")

    def test_success_confirms_email_without_creating_a_session(self):
        response = self.verify(self.token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "verified"})
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.email_verified_at)
        self.assertNotIn("sessionid", response.cookies)

    def test_expired_token(self):
        later = time.time() + MAX_AGE_SECONDS + 1
        with mock.patch("django.core.signing.time.time", return_value=later):
            response = self.verify(self.token)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_of(response)["code"], "invalid_token")
        self.user.refresh_from_db()
        self.assertIsNone(self.user.email_verified_at)

    def test_token_still_works_just_before_expiry(self):
        almost = time.time() + MAX_AGE_SECONDS - 60
        with mock.patch("django.core.signing.time.time", return_value=almost):
            response = self.verify(self.token)

        self.assertEqual(response.status_code, 200)

    def test_forged_token(self):
        forged = self.token[:-3] + ("abc" if not self.token.endswith("abc") else "xyz")

        self.assertEqual(error_of(self.verify(forged))["code"], "invalid_token")
        self.assertEqual(error_of(self.verify("garbage"))["code"], "invalid_token")

    def test_broken_tokens_always_give_invalid_token(self):
        half = self.token[: len(self.token) // 2]
        broken = {
            "truncated at '=' (cut email line)": half + "=",
            "newline inside": self.token[:20] + "\n" + self.token[20:],
            "space inside": self.token[:20] + " " + self.token[20:],
            "leading space": " garbage",
            "empty": "",
            "only spaces": "   ",
            "too long": "x" * 5000,
            "not a string": 12345,
            "null": None,
        }
        for name, value in broken.items():
            with self.subTest(name):
                response = self.verify(value)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(error_of(response)["code"], "invalid_token")

    def test_missing_token_and_non_object_body_give_invalid_token(self):
        for body in ({}, [], "text", ["a"]):
            with self.subTest(body=body):
                response = self.client.post(VERIFY, body, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertEqual(error_of(response)["code"], "invalid_token")

    def register(self, n):
        self.client.post(
            "/api/auth/register/",
            registration_payload(email=f"demo{n}@example.com", username=f"demouser{n}"),
            format="json",
        )

    def test_demo_link_is_logged_on_one_line_in_debug_and_with_demo_flag(self):
        for n, flags in enumerate([{"DEBUG": True}, {"DEBUG": False, "DEMO_LOG_VERIFY_LINKS": True}]):
            with self.subTest(flags), self.settings(**flags):
                with self.assertLogs("apps.users.services", "INFO") as logs:
                    self.register(n)
                line = next(m for m in logs.output if "DEMO link:" in m)
                self.assertIn("/verify-email/" + token_from_last_email(), line)
                self.assertNotIn("\n", line)

    def test_demo_link_is_not_logged_by_default(self):
        with self.settings(DEBUG=False, DEMO_LOG_VERIFY_LINKS=False):
            with self.assertNoLogs("apps.users.services", "INFO"):
                self.register(9)

    def test_token_with_another_salt_is_rejected(self):
        other = signing.dumps({"uid": self.user.pk, "email": self.user.email}, salt="something.else")

        self.assertEqual(error_of(self.verify(other))["code"], "invalid_token")

    def test_token_is_single_use(self):
        self.assertEqual(self.verify(self.token).status_code, 200)

        again = self.verify(self.token)

        self.assertEqual(again.status_code, 400)
        self.assertEqual(error_of(again)["code"], "invalid_token")

    def test_token_for_old_email_is_rejected(self):
        User.objects.filter(pk=self.user.pk).update(email="changed@example.com")

        self.assertEqual(error_of(self.verify(self.token))["code"], "invalid_token")

    def test_all_failures_look_the_same(self):
        self.verify(self.token)  # использован
        used = self.verify(self.token)
        forged = self.verify("garbage")
        with mock.patch("django.core.signing.time.time", return_value=time.time() + MAX_AGE_SECONDS + 1):
            expired = self.verify(self.token)

        self.assertEqual(used.json(), forged.json())
        self.assertEqual(used.json(), expired.json())


class ResendVerificationTests(APITestCase):
    def resend(self, email):
        return self.client.post(RESEND, {"email": email}, format="json")

    def test_unverified_account_gets_a_new_email(self):
        make_account(email="jane@example.com", verified=False)

        response = self.resend("Jane@Example.com")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {"status": "sent"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/verify-email/", mail.outbox[0].body)

    def test_same_response_for_unknown_and_verified_emails(self):
        make_account(email="verified@example.com")

        unknown = self.resend("nobody@example.com")
        verified = self.resend("verified@example.com")

        self.assertEqual(unknown.status_code, verified.status_code)
        self.assertEqual(unknown.json(), verified.json())
        self.assertEqual(len(mail.outbox), 0)  # писем нет
