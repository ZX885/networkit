import re
from unittest import mock

from django.contrib.sessions.models import Session
from django.core import mail, signing
from django.core.cache import cache
from django.test import Client, override_settings
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.users.tokens import RESET_SALT, make_reset_token, make_reset_uid

from .helpers import PASSWORD, error_of, field_codes, make_account

REQUEST = "/api/auth/password-reset/"
CONFIRM = "/api/auth/password-reset/confirm/"
NEW_PASSWORD = "Better-pass-4417!"


def reset_link_parts():
    """(uid, token) из ссылки в последнем письме."""
    match = re.search(r"/reset-password/([^/\s]+)/(\S+)", mail.outbox[-1].body)
    return match.group(1), match.group(2)


def ask(client, email):
    return client.post(REQUEST, {"email": email}, format="json")


def confirm(client, uid, token, new_password=NEW_PASSWORD):
    return client.post(
        CONFIRM, {"uid": uid, "token": token, "new_password": new_password}, format="json"
    )


class ResetRequestTests(APITestCase):
    def setUp(self):
        self.user = make_account(email="jane@example.com", username="janedoe", first_name="Jane")

    def test_existing_verified_user_gets_the_email(self):
        response = ask(self.client, "jane@example.com")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {"status": "sent"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["jane@example.com"])
        self.assertIn("/reset-password/", mail.outbox[0].body)
        self.assertIn("Hi Jane", mail.outbox[0].body)

    def test_response_is_identical_for_every_kind_of_address(self):
        make_account(email="new@example.com", username="newbie", verified=False)
        banned = make_account(email="banned@example.com", username="banned_one")
        User.objects.filter(pk=banned.pk).update(is_banned=True)

        responses = {
            email: ask(self.client, email)
            for email in (
                "jane@example.com",
                "nobody@example.com",
                "new@example.com",
                "banned@example.com",
                "JANE@Example.com",
            )
        }

        for email, response in responses.items():
            with self.subTest(email):
                self.assertEqual(response.status_code, 202)
                self.assertEqual(response.content, responses["nobody@example.com"].content)

    def test_email_goes_only_to_existing_verified_not_banned_users(self):
        make_account(email="new@example.com", username="newbie", verified=False)
        banned = make_account(email="banned@example.com", username="banned_one")
        User.objects.filter(pk=banned.pk).update(is_banned=True)

        for email in ("nobody@example.com", "new@example.com", "banned@example.com"):
            ask(self.client, email)

        self.assertEqual(mail.outbox, [])

    def test_email_is_matched_without_regard_to_case(self):
        ask(self.client, "JANE@EXAMPLE.COM")

        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_address_is_a_normal_validation_error(self):
        response = self.client.post(REQUEST, {"email": "not-an-email"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_of(response)["code"], "validation_error")

    def test_already_signed_in_user_can_ask_too(self):
        self.client.force_login(self.user)

        self.assertEqual(ask(self.client, "jane@example.com").status_code, 202)


class ResetConfirmTests(APITestCase):
    def setUp(self):
        self.user = make_account(email="jane@example.com", username="janedoe", first_name="Jane")
        ask(self.client, "jane@example.com")
        self.uid, self.token = reset_link_parts()
        mail.outbox.clear()

    def test_link_changes_the_password(self):
        response = confirm(self.client, self.uid, self.token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "password_changed"})
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))
        self.assertFalse(self.user.check_password(PASSWORD))

    def test_user_can_log_in_with_the_new_password(self):
        confirm(self.client, self.uid, self.token)

        login = self.client.post(
            "/api/auth/login/", {"email": "jane@example.com", "password": NEW_PASSWORD}, format="json"
        )

        self.assertEqual(login.status_code, 200)

    def test_link_works_only_once(self):
        first = confirm(self.client, self.uid, self.token)
        second = confirm(self.client, self.uid, self.token, new_password="Another-pass-9921!")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(error_of(second)["code"], "invalid_token")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

    def test_old_link_stops_working_after_the_password_was_changed_another_way(self):
        self.user.set_password("Changed-else-1234!")
        self.user.save()

        response = confirm(self.client, self.uid, self.token)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_of(response)["code"], "invalid_token")

    def test_old_link_stops_working_after_the_email_was_changed(self):
        User.objects.filter(pk=self.user.pk).update(email="other@example.com")

        self.assertEqual(confirm(self.client, self.uid, self.token).status_code, 400)

    def test_newer_link_works_and_replaces_nothing_else(self):
        ask(self.client, "jane@example.com")
        uid, token = reset_link_parts()

        self.assertEqual(confirm(self.client, uid, token).status_code, 200)
        self.assertEqual(confirm(self.client, self.uid, self.token).status_code, 400)

    def test_expired_link_is_rejected(self):
        with mock.patch("apps.users.tokens.RESET_MAX_AGE_SECONDS", -1):
            response = confirm(self.client, self.uid, self.token)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_of(response)["code"], "invalid_token")

    def test_forged_garbled_and_foreign_tokens_look_the_same(self):
        other = make_account(email="other@example.com", username="other_one")
        foreign = signing.dumps({"uid": self.user.pk}, salt="users.verify-email")
        wrong_salt = signing.dumps(
            {"uid": self.user.pk, "email": self.user.email, "ph": "x"}, salt="something.else"
        )
        for name, uid, token in (
            ("garbled", self.uid, "garbage"),
            ("tampered", self.uid, self.token[:-2] + "xx"),
            ("another users uid", make_reset_uid(other), self.token),
            ("verification token", self.uid, foreign),
            ("wrong salt", self.uid, wrong_salt),
            ("bad uid", "@@@", self.token),
            ("empty", "", ""),
        ):
            with self.subTest(name):
                response = confirm(self.client, uid, token)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(error_of(response)["code"], "invalid_token")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_missing_or_wrong_types_are_invalid_token(self):
        for body in ({}, {"uid": 1, "token": 2, "new_password": NEW_PASSWORD}, [1, 2]):
            with self.subTest(body):
                response = self.client.post(CONFIRM, body, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertEqual(error_of(response)["code"], "invalid_token")

    def test_banned_or_unverified_user_cannot_use_a_link(self):
        User.objects.filter(pk=self.user.pk).update(is_banned=True)
        self.assertEqual(error_of(confirm(self.client, self.uid, self.token))["code"], "invalid_token")
        User.objects.filter(pk=self.user.pk).update(is_banned=False, email_verified_at=None)
        self.assertEqual(error_of(confirm(self.client, self.uid, self.token))["code"], "invalid_token")

    def test_weak_new_password_is_rejected_and_the_link_survives(self):
        response = confirm(self.client, self.uid, self.token, new_password="aaaaaaa1")

        self.assertEqual(response.status_code, 400)
        self.assertIn("too_weak", field_codes(response, "new_password"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))
        self.assertEqual(confirm(self.client, self.uid, self.token).status_code, 200)  # ссылка жива

    def test_other_password_rules_apply(self):
        self.assertIn("too_common", field_codes(confirm(self.client, self.uid, self.token, "password"), "new_password"))
        self.assertIn(
            "too_similar",
            field_codes(confirm(self.client, self.uid, self.token, "janedoe123"), "new_password"),
        )
        self.assertIn(
            "entirely_numeric",
            field_codes(confirm(self.client, self.uid, self.token, "48172635"), "new_password"),
        )

    def test_bad_token_wins_over_a_weak_password(self):
        response = confirm(self.client, self.uid, "garbage", new_password="aaaaaaa1")

        self.assertEqual(error_of(response)["code"], "invalid_token")

    def test_all_sessions_of_the_user_are_deleted(self):
        phone, laptop, stranger = Client(), Client(), Client()
        phone.force_login(self.user)
        laptop.force_login(self.user)
        stranger.force_login(make_account(email="x@example.com", username="stranger"))
        self.assertEqual(Session.objects.count(), 3)

        confirm(self.client, self.uid, self.token)

        self.assertEqual(Session.objects.count(), 1)  # осталась только сессия постороннего
        self.assertEqual(phone.get("/api/me/").status_code, 401)
        self.assertEqual(laptop.get("/api/me/").status_code, 401)
        self.assertEqual(stranger.get("/api/me/").status_code, 200)

    def test_signed_in_user_session_is_ended_too(self):
        self.client.force_login(self.user)

        confirm(self.client, self.uid, self.token)

        self.assertEqual(self.client.get("/api/me/").status_code, 401)

    def test_notification_email_is_sent_without_links(self):
        confirm(self.client, self.uid, self.token)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["jane@example.com"])
        self.assertEqual(message.subject, "Your password was changed")
        self.assertIn("If this was not you, reset your password and contact support.", message.body)
        self.assertNotIn("http", message.body)

    def test_token_does_not_contain_the_password_hash(self):
        payload = signing.loads(make_reset_token(self.user), salt=RESET_SALT)

        self.assertNotIn(self.user.password, str(payload))
        self.assertEqual(payload["uid"], self.user.pk)


@override_settings(THROTTLING_ENABLED=True)
class ResetThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        make_account(email="jane@example.com", username="janedoe")

    def test_6th_request_in_an_hour_from_one_ip_is_throttled(self):
        for number in range(5):
            self.assertEqual(ask(self.client, f"user{number}@example.com").status_code, 202)

        response = ask(self.client, "another@example.com")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(error_of(response)["code"], "throttled")

    def test_6th_request_for_one_address_in_a_day_is_throttled_from_any_ip(self):
        from rest_framework.test import APIClient

        for number in range(5):
            client = APIClient(REMOTE_ADDR=f"10.0.0.{number + 1}")
            self.assertEqual(ask(client, "jane@example.com").status_code, 202)

        response = ask(APIClient(REMOTE_ADDR="10.0.0.99"), "JANE@example.com")

        self.assertEqual(response.status_code, 429)

    def test_limit_applies_to_unknown_addresses_equally(self):
        from rest_framework.test import APIClient

        for number in range(5):
            ask(APIClient(REMOTE_ADDR=f"10.0.1.{number + 1}"), "ghost@example.com")

        self.assertEqual(ask(APIClient(REMOTE_ADDR="10.0.1.99"), "ghost@example.com").status_code, 429)

    def test_confirm_has_its_own_limit_by_ip(self):
        for _ in range(30):
            confirm(self.client, "x", "y")

        self.assertEqual(confirm(self.client, "x", "y").status_code, 429)
