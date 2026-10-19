import re
from unittest import mock

from django.core import mail, signing
from django.core.cache import cache
from django.test import Client, override_settings
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.users.tokens import EMAIL_CHANGE_SALT, make_email_change_token

from .helpers import PASSWORD, error_of, field_codes, make_account

REQUEST = "/api/auth/email/change/"
CONFIRM = "/api/auth/email/change/confirm/"


def ask(client, new_email="new@example.com", password=PASSWORD):
    return client.post(REQUEST, {"new_email": new_email, "password": password}, format="json")


def token_from(message):
    return re.search(r"/confirm-email-change/(\S+)", message.body).group(1)


def confirm(client, token):
    return client.post(CONFIRM, {"token": token}, format="json")


class EmailChangeRequestTests(APITestCase):
    def setUp(self):
        self.user = make_account(email="jane@example.com", username="janedoe", first_name="Jane")
        self.client.force_login(self.user)

    def test_request_sends_a_link_to_the_new_address_and_a_notice_to_the_old_one(self):
        response = ask(self.client)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {"status": "verification_sent"})
        by_recipient = {message.to[0]: message for message in mail.outbox}
        self.assertEqual(set(by_recipient), {"new@example.com", "jane@example.com"})
        self.assertIn("/confirm-email-change/", by_recipient["new@example.com"].body)
        self.assertIn("new@example.com", by_recipient["jane@example.com"].body)
        self.assertNotIn("/confirm-email-change/", by_recipient["jane@example.com"].body)

    def test_email_stays_the_same_until_confirmed(self):
        ask(self.client)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "jane@example.com")
        self.assertEqual(self.user.pending_email, "new@example.com")

    def test_new_address_is_normalized(self):
        ask(self.client, new_email="  New@Example.COM ")

        self.user.refresh_from_db()
        self.assertEqual(self.user.pending_email, "new@example.com")

    def test_wrong_password_is_a_field_error(self):
        response = ask(self.client, password="Wrong-pass-9911!")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "password"), ["incorrect"])
        self.assertEqual(mail.outbox, [])
        self.user.refresh_from_db()
        self.assertIsNone(self.user.pending_email)

    def test_invalid_address_is_a_validation_error(self):
        response = ask(self.client, new_email="nope")

        self.assertEqual(response.status_code, 400)
        self.assertIn("new_email", error_of(response)["fields"])

    def test_taken_address_gets_the_same_response_and_a_different_email(self):
        make_account(email="busy@example.com", username="busy_one")
        free = ask(self.client, "free@example.com")
        free_status, free_content = free.status_code, free.content
        mail.outbox.clear()

        taken = ask(self.client, "BUSY@example.com")

        self.assertEqual((taken.status_code, taken.content), (free_status, free_content))
        recipients = sorted(message.to[0] for message in mail.outbox)
        self.assertEqual(recipients, ["busy@example.com", "jane@example.com"])
        busy_mail = next(m for m in mail.outbox if m.to == ["busy@example.com"])
        self.assertIn("already belongs to an account", busy_mail.body)
        self.assertNotIn("/confirm-email-change/", busy_mail.body)
        self.user.refresh_from_db()
        self.assertEqual(self.user.pending_email, "free@example.com")  # занятый адрес не записан

    def test_taken_address_does_not_overwrite_pending_email(self):
        make_account(email="busy@example.com", username="busy_one")

        ask(self.client, "busy@example.com")

        self.user.refresh_from_db()
        self.assertIsNone(self.user.pending_email)

    def test_own_address_gives_the_same_response_and_changes_nothing(self):
        response = ask(self.client, "jane@example.com")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(mail.outbox, [])
        self.user.refresh_from_db()
        self.assertIsNone(self.user.pending_email)

    def test_anonymous_gets_401(self):
        self.client.logout()

        self.assertEqual(ask(self.client).status_code, 401)

    def test_sessions_are_not_touched(self):
        other = Client()
        other.force_login(self.user)

        ask(self.client)

        self.assertEqual(other.get("/api/me/").status_code, 200)


class EmailChangeConfirmTests(APITestCase):
    def setUp(self):
        self.user = make_account(email="jane@example.com", username="janedoe")
        self.client.force_login(self.user)
        ask(self.client)
        self.token = token_from(next(m for m in mail.outbox if m.to == ["new@example.com"]))
        mail.outbox.clear()

    def test_link_changes_the_email_and_marks_it_verified(self):
        User.objects.filter(pk=self.user.pk).update(email_verified_at=None)

        response = confirm(Client(), self.token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "email_changed"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")
        self.assertIsNotNone(self.user.email_verified_at)
        self.assertIsNone(self.user.pending_email)

    def test_previous_address_gets_a_notification_after_the_change(self):
        confirm(Client(), self.token)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["jane@example.com"])
        self.assertEqual(message.subject, "Your email was changed")
        self.assertIn("new@example.com", message.body)
        self.assertIn("reset your password and contact support", message.body)
        self.assertNotIn("http", message.body)

    def test_no_notification_when_the_link_is_rejected(self):
        confirm(Client(), "garbage")
        confirm(Client(), self.token)
        mail.outbox.clear()
        confirm(Client(), self.token)  # повторное использование

        self.assertEqual(mail.outbox, [])

    def test_sessions_stay_after_the_change(self):
        confirm(Client(), self.token)

        self.assertEqual(self.client.get("/api/me/").status_code, 200)

    def test_can_log_in_with_the_new_address_only(self):
        confirm(Client(), self.token)
        fresh = Client()

        old = fresh.post("/api/auth/login/", {"email": "jane@example.com", "password": PASSWORD}, content_type="application/json")
        new = fresh.post("/api/auth/login/", {"email": "new@example.com", "password": PASSWORD}, content_type="application/json")

        self.assertEqual((old.status_code, new.status_code), (400, 200))

    def test_link_works_only_once(self):
        first = confirm(Client(), self.token)
        second = confirm(Client(), self.token)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(error_of(second)["code"], "invalid_token")

    def test_link_works_without_being_signed_in(self):
        self.assertEqual(confirm(Client(), self.token).status_code, 200)

    def test_new_request_invalidates_the_old_link(self):
        ask(self.client, "third@example.com")

        old = confirm(Client(), self.token)

        self.assertEqual(old.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "jane@example.com")
        self.assertEqual(self.user.pending_email, "third@example.com")

    def test_forged_foreign_expired_and_garbled_tokens_look_the_same(self):
        verification = signing.dumps({"uid": self.user.pk, "email": "new@example.com"}, salt="users.verify-email")
        wrong_salt = signing.dumps({"uid": self.user.pk, "new_email": "new@example.com"}, salt="other")
        for name, token in (
            ("garbled", "garbage"),
            ("empty", ""),
            ("tampered", self.token[:-2] + "xx"),
            ("verification token", verification),
            ("wrong salt", wrong_salt),
        ):
            with self.subTest(name):
                response = confirm(Client(), token)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(error_of(response)["code"], "invalid_token")
        with mock.patch("apps.users.tokens.EMAIL_CHANGE_MAX_AGE_SECONDS", -1):
            self.assertEqual(error_of(confirm(Client(), self.token))["code"], "invalid_token")
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "jane@example.com")

    def test_wrong_types_in_the_body(self):
        for body in ({}, {"token": 5}, ["x"]):
            with self.subTest(body):
                response = Client().post(CONFIRM, body, content_type="application/json")
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["error"]["code"], "invalid_token")

    def test_token_for_someone_elses_pending_address_is_rejected(self):
        other = make_account(email="other@example.com", username="other_one")
        # Токен подписан верно, но pending_email у этого пользователя не совпадает
        forged = make_email_change_token(other, "new@example.com")

        response = confirm(Client(), forged)

        self.assertEqual(response.status_code, 400)
        other.refresh_from_db()
        self.assertEqual(other.email, "other@example.com")

    def test_address_taken_in_the_meantime_is_rejected(self):
        make_account(email="new@example.com", username="late_one")

        response = confirm(Client(), self.token)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_of(response)["code"], "invalid_token")
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "jane@example.com")

    def test_token_payload_has_no_password(self):
        payload = signing.loads(self.token, salt=EMAIL_CHANGE_SALT)

        self.assertEqual(set(payload), {"uid", "new_email"})


@override_settings(THROTTLING_ENABLED=True)
class EmailChangeThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = make_account(email="jane@example.com", username="janedoe")
        self.client.force_login(self.user)

    def test_6th_request_in_an_hour_is_throttled(self):
        for number in range(5):
            self.assertEqual(ask(self.client, f"new{number}@example.com").status_code, 202)

        response = ask(self.client, "new9@example.com")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(error_of(response)["code"], "throttled")

    def test_confirm_is_limited_by_ip(self):
        for _ in range(30):
            confirm(self.client, "garbage")

        self.assertEqual(confirm(self.client, "garbage").status_code, 429)
