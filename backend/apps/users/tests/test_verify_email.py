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
