"""Сила пароля: формула, валидатор, регистрация. Таблица паролей (password_cases.json) общая с frontend:
тот же файл проверяет node-скрипт для frontend/src/lib/passwordStrength.js."""

import json
import logging
from pathlib import Path

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.users.password_strength import character_classes, password_strength

from .helpers import PASSWORD, error_of, field_codes, registration_payload

URL = "/api/auth/register/"
CASES = json.loads((Path(__file__).parent / "password_cases.json").read_text(encoding="utf-8"))


class StrengthFormulaTests(APITestCase):
    def test_table_of_passwords(self):
        for case in CASES:
            with self.subTest(password=case["password"], expected=case["level"]):
                self.assertEqual(password_strength(case["password"]), case["level"])

    def test_table_covers_every_level_and_the_boundaries(self):
        levels = {case["level"] for case in CASES}
        passwords = {case["password"] for case in CASES}

        self.assertEqual(levels, {"weak", "medium", "strong"})
        self.assertGreaterEqual(len(CASES), 25)
        for boundary in ("abcdefg1", "Abcdef1", "Abcdefgh1jk", "Abcdefgh1jkl", "abcdefgh1jklmno",
                         "abcdefgh1jklmnop", "aaaaaaa1", "11111111a", "ababababab12"):
            self.assertIn(boundary, passwords)

    def test_four_different_characters_are_required(self):
        self.assertEqual(password_strength("aaaaaaa1"), "weak")  # 2 разных символа
        self.assertEqual(password_strength("11111111a"), "weak")
        self.assertEqual(password_strength("abababab12"), "medium")  # 4 разных (a, b, 1, 2)
        self.assertEqual(password_strength("aabbaab1"), "weak")  # 3 разных (a, b, 1)

    def test_length_counts_unicode_code_points(self):
        self.assertEqual(len("😀😁😂🤣😃😄😅a"), 8)  # 8 символов, а не 16 единиц UTF-16
        self.assertEqual(password_strength("😀😁😂🤣😃😄😅a"), "medium")
        self.assertEqual(password_strength("😀😁😂🤣😃😄😅"), "weak")  # 7 символов

    def test_character_classes(self):
        self.assertEqual(character_classes(""), 0)
        self.assertEqual(character_classes("abc"), 1)
        self.assertEqual(character_classes("aB"), 2)
        self.assertEqual(character_classes("aB1"), 3)
        self.assertEqual(character_classes("aB1 "), 4)
        self.assertEqual(character_classes("Пароль1"), 3)
        self.assertEqual(character_classes("密码"), 1)  # иероглифы — «прочие»


class ValidatorTests(APITestCase):
    def test_weak_password_is_rejected_with_the_expected_code(self):
        with self.assertRaises(ValidationError) as caught:
            password_validation.validate_password("aaaaaaa1")

        codes = [error.code for error in caught.exception.error_list]
        self.assertIn("password_too_weak", codes)

    def test_medium_and_strong_pass_the_strength_validator(self):
        for password in ("kx9mqz4w", "Tr0ub4dor&3-horse"):
            with self.subTest(password):
                try:
                    password_validation.validate_password(password)
                except ValidationError as error:
                    self.assertNotIn("password_too_weak", [e.code for e in error.error_list])

    def test_message_does_not_contain_the_password(self):
        secret = "aaaaaaa1-secret-text"
        with self.assertRaises(ValidationError) as caught:
            password_validation.validate_password("qqqqqqq1")

        for error in caught.exception.error_list:
            self.assertNotIn("qqqqqqq1", str(error.message))
            self.assertNotIn(secret, str(error.params))


class RegistrationStrengthTests(APITestCase):
    def post(self, password, **overrides):
        return self.client.post(URL, registration_payload(password=password, **overrides), format="json")

    def test_weak_password_gives_400_too_weak_on_the_password_field(self):
        for password in ("aaaaaaa1", "11111111a", "Abcdef1", "abcdefghijkl"):
            with self.subTest(password):
                response = self.post(password)

                self.assertEqual(response.status_code, 400)
                self.assertIn("too_weak", field_codes(response, "password"))
        self.assertFalse(User.objects.exists())

    def test_error_text_does_not_contain_the_password(self):
        response = self.post("aaaaaaa1")

        self.assertNotIn("aaaaaaa1", response.content.decode())

    def test_medium_password_is_accepted(self):
        response = self.post("kx9mqz4w")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email="jane@example.com").exists())

    def test_strong_password_is_accepted(self):
        self.assertEqual(self.post("Tr0ub4dor&3-horse").status_code, 201)

    def test_default_test_password_is_strong(self):
        self.assertEqual(password_strength(PASSWORD), "strong")

    def test_other_password_checks_still_work(self):
        self.assertIn("too_common", field_codes(self.post("password"), "password"))
        self.assertIn("entirely_numeric", field_codes(self.post("48172635"), "password"))
        self.assertIn("too_short", field_codes(self.post("abc12"), "password"))
        similar = self.post("janedoe123", email="janedoe@example.com")
        self.assertIn("too_similar", field_codes(similar, "password"))

    def test_weak_and_common_password_reports_both_codes(self):
        codes = field_codes(self.post("password"), "password")

        self.assertIn("too_common", codes)
        self.assertIn("too_weak", codes)

    def test_response_keeps_the_usual_error_format(self):
        error = error_of(self.post("aaaaaaa1"))

        self.assertEqual(error["code"], "validation_error")
        item = next(i for i in error["fields"]["password"] if i["code"] == "too_weak")
        self.assertTrue(item["message"].startswith("This password is too weak"))


class PasswordNeverLoggedTests(APITestCase):
    SECRET = "Zq7!secretPassw0rd-do-not-log"

    def captured(self, logs):
        formatter = logging.Formatter()
        return "\n".join(formatter.format(record) for record in logs.records)

    def test_weak_registration_does_not_log_the_password(self):
        weak = "zzzzzzz1"
        with self.assertLogs(level="DEBUG") as logs:
            logging.getLogger("probe").debug("start")  # assertLogs требует хотя бы одну запись
            self.client.post(URL, registration_payload(password=weak), format="json")

        self.assertNotIn(weak, self.captured(logs))

    def test_successful_registration_does_not_log_the_password(self):
        with self.assertLogs(level="DEBUG") as logs:
            logging.getLogger("probe").debug("start")
            self.client.post(URL, registration_payload(password=self.SECRET), format="json")

        self.assertNotIn(self.SECRET, self.captured(logs))

    def test_unexpected_error_during_registration_does_not_log_the_password(self):
        from unittest import mock

        with mock.patch(
            "apps.users.views.services.register_account", side_effect=RuntimeError("boom")
        ), self.assertLogs(level="ERROR") as logs:
            response = self.client.post(URL, registration_payload(password=self.SECRET), format="json")

        self.assertEqual(response.status_code, 500)
        self.assertNotIn(self.SECRET, self.captured(logs))
        self.assertNotIn(self.SECRET, response.content.decode())
