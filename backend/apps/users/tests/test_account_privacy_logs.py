"""Пароли, токены и адреса из писем не попадают в логи и трейсбеки."""

import logging
from unittest import mock

from django.core import mail
from django.db import DatabaseError
from rest_framework.test import APITestCase

from config.exceptions import PRIVATE_PATH_PREFIXES

from .helpers import PASSWORD, make_account, registration_payload

SECRET = "Zq7!secretPassw0rd-do-not-log"
TOKEN = "SECRET-token-value-12345"


def logged_text(logs):
    formatter = logging.Formatter()
    return "\n".join(formatter.format(record) for record in logs.records)


class PrefixTests(APITestCase):
    def test_all_account_paths_are_private(self):
        for path in (
            "/api/auth/login/",
            "/api/auth/register/",
            "/api/auth/password-reset/",
            "/api/auth/password-reset/confirm/",
            "/api/auth/password/change/",
            "/api/auth/email/change/",
            "/api/auth/email/change/confirm/",
            "/api/me/",
            "/api/conversations/",
        ):
            with self.subTest(path):
                self.assertTrue(path.startswith(PRIVATE_PATH_PREFIXES), path)

    def test_public_paths_are_not_redacted(self):
        for path in ("/api/profiles/", "/api/meta/", "/api/auth/csrf/"):
            self.assertFalse(path.startswith(PRIVATE_PATH_PREFIXES), path)


class ErrorsDoNotLeakTests(APITestCase):
    def setUp(self):
        self.user = make_account(email="jane@example.com", username="janedoe")
        self.client.force_login(self.user)

    def fail(self, target, method, path, body):
        with mock.patch(target, side_effect=DatabaseError(f"Failing row contains ({SECRET}, {TOKEN})")):
            with self.assertLogs(level="ERROR") as logs:
                response = getattr(self.client, method)(path, body, format="json")
        self.assertEqual(response.status_code, 500)
        text = logged_text(logs)
        self.assertNotIn(SECRET, text)
        self.assertNotIn(TOKEN, text)
        self.assertNotIn(SECRET, response.content.decode())
        self.assertIn("RedactedError", text)

    def test_password_change_failure(self):
        self.fail(
            "apps.users.views.services.change_password",
            "post",
            "/api/auth/password/change/",
            {"old_password": PASSWORD, "new_password": SECRET},
        )

    def test_password_reset_failure(self):
        self.fail(
            "apps.users.views.services.request_password_reset",
            "post",
            "/api/auth/password-reset/",
            {"email": "jane@example.com"},
        )

    def test_reset_confirm_failure(self):
        self.fail(
            "apps.users.views.services.reset_password",
            "post",
            "/api/auth/password-reset/confirm/",
            {"uid": "x", "token": TOKEN, "new_password": SECRET},
        )

    def test_email_change_failure(self):
        self.fail(
            "apps.users.views.services.request_email_change",
            "post",
            "/api/auth/email/change/",
            {"new_email": "new@example.com", "password": PASSWORD},
        )

    def test_email_confirm_failure(self):
        self.fail(
            "apps.users.views.services.confirm_email_change",
            "post",
            "/api/auth/email/change/confirm/",
            {"token": TOKEN},
        )

    def test_delete_failure(self):
        self.fail(
            "apps.profiles.views.account_services.delete_account",
            "delete",
            "/api/me/",
            {"password": PASSWORD},
        )

    def test_login_and_register_failures(self):
        self.client.logout()
        self.fail("apps.users.views.authenticate", "post", "/api/auth/login/", {"email": "jane@example.com", "password": SECRET})
        self.fail(
            "apps.users.views.services.register_account",
            "post",
            "/api/auth/register/",
            registration_payload(email="a@example.com", username="newperson", password=SECRET),
        )


class SuccessfulFlowsDoNotLogSecretsTests(APITestCase):
    NEW = "Better-pass-4417!"

    def setUp(self):
        self.user = make_account(email="jane@example.com", username="janedoe")

    def run_flow(self):
        """Сброс пароля, смена пароля, смена email и удаление: всё одним проходом."""
        import re

        self.client.post("/api/auth/password-reset/", {"email": "jane@example.com"}, format="json")
        uid, token = re.search(r"/reset-password/([^/\s]+)/(\S+)", mail.outbox[-1].body).groups()
        self.client.post(
            "/api/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": self.NEW},
            format="json",
        )
        self.client.post("/api/auth/login/", {"email": "jane@example.com", "password": self.NEW}, format="json")
        self.client.post(
            "/api/auth/password/change/", {"old_password": self.NEW, "new_password": SECRET}, format="json"
        )
        self.client.post(
            "/api/auth/email/change/", {"new_email": "new@example.com", "password": SECRET}, format="json"
        )
        confirm_mail = next(m for m in reversed(mail.outbox) if "/confirm-email-change/" in m.body)
        email_token = re.search(r"/confirm-email-change/(\S+)", confirm_mail.body).group(1)
        self.client.post("/api/auth/email/change/confirm/", {"token": email_token}, format="json")
        self.client.delete("/api/me/", {"password": SECRET}, format="json")
        return token, email_token

    def test_no_log_record_contains_passwords_or_tokens(self):
        with self.assertLogs(level="DEBUG") as logs:
            logging.getLogger("probe").debug("start")
            reset_token, email_token = self.run_flow()

        text = logged_text(logs)
        for secret in (self.NEW, SECRET, PASSWORD, reset_token, email_token):
            self.assertNotIn(secret, text)

    def test_demo_links_are_logged_only_on_demand_and_without_passwords(self):
        from django.test import override_settings

        with override_settings(DEMO_LOG_VERIFY_LINKS=True), self.assertLogs("apps.users.services", "INFO") as logs:
            self.client.post("/api/auth/password-reset/", {"email": "jane@example.com"}, format="json")

        lines = [r.getMessage() for r in logs.records]
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("DEMO link: "))
        self.assertIn("/reset-password/", lines[0])
        self.assertNotIn(PASSWORD, lines[0])
