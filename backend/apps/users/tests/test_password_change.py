from django.contrib.sessions.models import Session
from django.core import mail
from django.core.cache import cache
from django.test import Client, override_settings
from rest_framework.test import APITestCase

from .helpers import PASSWORD, error_of, field_codes, make_account

URL = "/api/auth/password/change/"
NEW_PASSWORD = "Better-pass-4417!"


def change(client, old=PASSWORD, new=NEW_PASSWORD):
    return client.post(URL, {"old_password": old, "new_password": new}, format="json")


class PasswordChangeTests(APITestCase):
    def setUp(self):
        self.user = make_account(email="jane@example.com", username="janedoe", first_name="Jane")
        self.client.force_login(self.user)

    def test_password_is_changed_with_204_and_no_body(self):
        response = change(self.client)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

    def test_wrong_old_password_is_a_field_error_with_code_incorrect(self):
        response = change(self.client, old="Wrong-old-pass-1!")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_of(response)["code"], "validation_error")
        self.assertEqual(field_codes(response, "old_password"), ["incorrect"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_weak_new_password_is_rejected(self):
        response = change(self.client, new="aaaaaaa1")

        self.assertEqual(response.status_code, 400)
        self.assertIn("too_weak", field_codes(response, "new_password"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_other_password_rules_apply(self):
        self.assertIn("too_common", field_codes(change(self.client, new="password"), "new_password"))
        self.assertIn("too_similar", field_codes(change(self.client, new="janedoe123"), "new_password"))
        self.assertIn("too_similar", field_codes(change(self.client, new="jane-example"), "new_password"))
        self.assertIn("entirely_numeric", field_codes(change(self.client, new="48172635"), "new_password"))
        self.assertIn("too_short", field_codes(change(self.client, new="abc12"), "new_password"))

    def test_both_errors_are_reported_together(self):
        response = change(self.client, old="Wrong-old-pass-1!", new="aaaaaaa1")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "old_password"), ["incorrect"])
        self.assertIn("too_weak", field_codes(response, "new_password"))

    def test_missing_fields(self):
        response = self.client.post(URL, {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "old_password"), ["required"])
        self.assertEqual(field_codes(response, "new_password"), ["required"])

    def test_current_session_stays_and_others_are_deleted(self):
        other_phone, other_laptop = Client(), Client()
        other_phone.force_login(self.user)
        other_laptop.force_login(self.user)
        stranger = Client()
        stranger.force_login(make_account(email="x@example.com", username="stranger"))
        self.assertEqual(Session.objects.count(), 4)

        change(self.client)

        self.assertEqual(self.client.get("/api/me/").status_code, 200)  # текущая сессия жива
        self.assertEqual(other_phone.get("/api/me/").status_code, 401)
        self.assertEqual(other_laptop.get("/api/me/").status_code, 401)
        self.assertEqual(stranger.get("/api/me/").status_code, 200)
        self.assertEqual(Session.objects.count(), 2)  # текущая и сессия постороннего

    def test_current_session_works_for_writes_after_the_change(self):
        change(self.client)

        self.assertEqual(self.client.patch("/api/me/", {"bio": "still here"}, format="json").status_code, 200)

    def test_can_log_in_with_the_new_password_only(self):
        change(self.client)
        fresh = Client()

        old = fresh.post("/api/auth/login/", {"email": "jane@example.com", "password": PASSWORD}, content_type="application/json")
        new = fresh.post("/api/auth/login/", {"email": "jane@example.com", "password": NEW_PASSWORD}, content_type="application/json")

        self.assertEqual((old.status_code, new.status_code), (400, 200))

    def test_notification_email_is_sent_only_on_success(self):
        change(self.client, old="Wrong-old-pass-1!")
        self.assertEqual(mail.outbox, [])

        change(self.client)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Your password was changed")
        self.assertEqual(mail.outbox[0].to, ["jane@example.com"])
        self.assertNotIn("http", mail.outbox[0].body)

    def test_anonymous_gets_401(self):
        self.client.logout()

        self.assertEqual(change(self.client).status_code, 401)

    def test_new_password_cannot_equal_the_old_one(self):
        response = change(self.client, new=PASSWORD)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "new_password"), ["same_as_old"])
        self.assertEqual(mail.outbox, [])

    def test_same_as_old_is_not_reported_when_the_old_password_is_wrong(self):
        response = change(self.client, old="Wrong-old-pass-1!", new="Wrong-old-pass-1!")

        self.assertEqual(field_codes(response, "old_password"), ["incorrect"])
        self.assertNotIn("new_password", error_of(response)["fields"])


@override_settings(THROTTLING_ENABLED=True)
class PasswordChangeThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = make_account(email="jane@example.com", username="janedoe")
        self.client.force_login(self.user)

    def test_11th_attempt_in_an_hour_is_throttled(self):
        for _ in range(10):
            self.assertEqual(change(self.client, old="Wrong-old-pass-1!").status_code, 400)

        response = change(self.client)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(error_of(response)["code"], "throttled")

    def test_limit_is_per_user(self):
        for _ in range(10):
            change(self.client, old="Wrong-old-pass-1!")
        other = make_account(email="other@example.com", username="other_one")
        self.client.force_login(other)

        self.assertEqual(change(self.client).status_code, 204)

    def test_limit_is_shared_with_other_password_checks(self):
        for _ in range(10):
            change(self.client, old="Wrong-old-pass-1!")

        response = self.client.delete("/api/me/", {"password": PASSWORD}, format="json")

        self.assertEqual(response.status_code, 429)
