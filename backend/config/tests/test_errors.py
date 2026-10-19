"""Единый формат ошибок API (docs/SPEC.md §3.0)."""

import json
from unittest import mock

from django.test import RequestFactory
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.profiles.tests.factories import make_user
from apps.users.tests.helpers import error_of
from config.exceptions import normalize_code, server_error_view


class ErrorFormatTests(APITestCase):
    def assert_shape(self, response, status, code, keys=("code", "message")):
        self.assertEqual(response.status_code, status)
        self.assertEqual(list(response.json()), ["error"])  # ровно один ключ верхнего уровня
        self.assertEqual(set(error_of(response)), set(keys))
        self.assertEqual(error_of(response)["code"], code)
        self.assertIsInstance(error_of(response)["message"], str)

    def test_validation_error(self):
        response = self.client.post("/api/auth/register/", {}, format="json")

        self.assert_shape(response, 400, "validation_error", ("code", "message", "fields", "non_field_errors"))
        self.assertEqual(error_of(response)["non_field_errors"], [])
        entry = error_of(response)["fields"]["email"][0]
        self.assertEqual(set(entry), {"code", "message"})
        self.assertEqual(entry["code"], "required")

    def test_malformed_json(self):
        response = self.client.post("/api/auth/register/", "{bad json", content_type="application/json")

        self.assert_shape(response, 400, "validation_error", ("code", "message", "fields", "non_field_errors"))
        self.assertEqual(error_of(response)["non_field_errors"][0]["code"], "parse_error")

    def test_not_authenticated(self):
        response = self.client.get("/api/me/")

        self.assert_shape(response, 401, "not_authenticated")
        self.assertIn("WWW-Authenticate", response)

    def test_not_found_is_json_for_api_and_html_otherwise(self):
        api = self.client.get("/api/no-such-endpoint/")
        site = self.client.get("/no-such-page/")

        self.assert_shape(api, 404, "not_found")
        self.assertEqual(site.status_code, 404)
        self.assertIn("text/html", site["Content-Type"])

    def test_method_not_allowed(self):
        response = self.client.get("/api/auth/register/")

        self.assert_shape(response, 405, "method_not_allowed")

    def test_permission_denied(self):
        # Аккаунт без профиля (например, суперпользователь) не может войти через API
        make_user(email="staff@example.com", password="S3cure-pass-77", email_verified_at=timezone.now())

        response = self.client.post(
            "/api/auth/login/", {"email": "staff@example.com", "password": "S3cure-pass-77"}, format="json"
        )

        self.assert_shape(response, 403, "permission_denied")

    def test_csrf_failed(self):
        client = self.client_class(enforce_csrf_checks=True)

        response = client.post("/api/auth/login/", {"email": "a@example.com", "password": "x"}, format="json")

        self.assert_shape(response, 403, "csrf_failed")

    def test_server_error_has_no_details(self):
        request = RequestFactory().get("/api/anything/")

        response = server_error_view(request)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content),
            {"error": {"code": "server_error", "message": "Something went wrong."}},
        )

    def test_unhandled_exception_is_logged_with_traceback_and_hidden_from_client(self):
        self.client.force_login(make_user(email="crash@example.com"))

        with mock.patch("apps.profiles.views.ProfileListView.get", side_effect=RuntimeError("secret boom")):
            with self.assertLogs("config.exceptions", "ERROR") as logs:
                response = self.client.get("/api/profiles/")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {"error": {"code": "server_error", "message": "Something went wrong."}},
        )
        self.assertNotIn("secret boom", response.content.decode())  # клиент не видит причину
        record = logs.records[0]
        self.assertIsNotNone(record.exc_info)  # в логе есть трейсбек
        self.assertIn("GET /api/profiles/", record.getMessage())
        self.assertIn("secret boom", str(record.exc_info[1]))

    def test_server_error_for_site_pages_is_html(self):
        response = server_error_view(RequestFactory().get("/some-page/"))

        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Server Error", response.content)


class CodeNormalizationTests(APITestCase):
    def test_codes_are_mapped_to_the_spec(self):
        self.assertEqual(normalize_code("blank"), "required")
        self.assertEqual(normalize_code("null"), "required")
        self.assertEqual(normalize_code("max_length"), "too_long")
        self.assertEqual(normalize_code("password_too_short"), "too_short")
        self.assertEqual(normalize_code("password_entirely_numeric"), "entirely_numeric")
        self.assertEqual(normalize_code("invalid_choice"), "invalid_choice")
