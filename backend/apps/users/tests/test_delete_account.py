import unittest
from unittest import mock

from django.apps import apps
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.test import Client, override_settings
from rest_framework.test import APITestCase

from apps.messaging.models import Conversation, Message
from apps.messaging.tests.helpers import make_conversation
from apps.profiles.models import Profile, SavedProfile
from apps.users.models import User

from .helpers import PASSWORD, error_of, field_codes, make_account

ME = "/api/me/"
MODERATION = apps.is_installed("apps.moderation")


def delete(client, password=PASSWORD):
    return client.delete(ME, {"password": password}, format="json")


class DeleteAccountTests(APITestCase):
    def setUp(self):
        self.user = make_account(email="jane@example.com", username="janedoe")
        self.client.force_login(self.user)

    def test_account_is_deleted_with_204_and_no_body(self):
        response = delete(self.client)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(User.objects.filter(email="jane@example.com").exists())
        self.assertFalse(Profile.objects.filter(username="janedoe").exists())

    def test_wrong_password_is_a_field_error_and_nothing_is_deleted(self):
        response = delete(self.client, "Wrong-pass-9911!")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "password"), ["incorrect"])
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        self.assertEqual(self.client.get(ME).status_code, 200)

    def test_missing_or_non_string_password(self):
        self.assertEqual(field_codes(self.client.delete(ME, {}, format="json"), "password"), ["required"])
        self.assertEqual(self.client.delete(ME, {"password": 5}, format="json").status_code, 400)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_user_is_logged_out_and_the_second_delete_is_401(self):
        delete(self.client)

        self.assertEqual(self.client.get(ME).status_code, 401)
        self.assertEqual(delete(self.client).status_code, 401)

    def test_all_sessions_of_the_user_are_deleted_and_others_stay(self):
        phone = Client()
        phone.force_login(self.user)
        stranger = Client()
        stranger.force_login(make_account(email="x@example.com", username="stranger"))
        self.assertEqual(Session.objects.count(), 3)

        delete(self.client)

        self.assertEqual(Session.objects.count(), 1)
        self.assertEqual(phone.get(ME).status_code, 401)
        self.assertEqual(stranger.get(ME).status_code, 200)

    def test_profile_is_gone_from_search_and_login_is_impossible(self):
        viewer = make_account(email="viewer@example.com", username="viewer_one")
        delete(self.client)
        other = Client()
        other.force_login(viewer)

        search = other.get("/api/profiles/").json()["results"]
        profile = other.get("/api/profiles/janedoe/")
        login = Client().post(
            "/api/auth/login/", {"email": "jane@example.com", "password": PASSWORD}, content_type="application/json"
        )

        self.assertNotIn("janedoe", [item["username"] for item in search])
        self.assertEqual(profile.status_code, 404)
        self.assertEqual(login.status_code, 400)

    def test_staff_and_superusers_cannot_delete_themselves_through_the_api(self):
        staff = User.objects.create_user(email="staff@example.com", password=PASSWORD, is_staff=True)
        boss = User.objects.create_superuser(email="boss@example.com", password=PASSWORD)
        for user in (staff, boss):
            with self.subTest(user.email):
                client = Client()
                client.force_login(user)
                response = client.delete(ME, {"password": PASSWORD}, content_type="application/json")
                self.assertEqual(response.status_code, 403)
                self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_extension_point_for_files_is_called_after_the_deletion(self):
        with mock.patch("apps.users.services.delete_account_files") as hook:
            with self.captureOnCommitCallbacks(execute=True):
                delete(self.client)

        hook.assert_called_once_with(self.user.pk)

    def test_deletion_is_atomic(self):
        with mock.patch("apps.users.services.delete_user_sessions", side_effect=RuntimeError("boom")):
            response = delete(self.client)

        self.assertEqual(response.status_code, 500)

        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        self.assertTrue(Profile.objects.filter(username="janedoe").exists())


class CascadeTests(APITestCase):
    """Что именно удаляется вместе с аккаунтом."""

    def setUp(self):
        self.user = make_account(email="jane@example.com", username="janedoe")
        self.friend = make_account(email="friend@example.com", username="friend_one")
        self.client.force_login(self.user)

    def test_saved_profiles_are_deleted_in_both_directions(self):
        SavedProfile.objects.create(owner=self.user, saved_user=self.friend)
        SavedProfile.objects.create(owner=self.friend, saved_user=self.user)

        delete(self.client)

        self.assertFalse(SavedProfile.objects.exists())
        self.assertTrue(User.objects.filter(pk=self.friend.pk).exists())  # собеседник остаётся

    def test_conversations_and_messages_are_deleted_for_both_sides(self):
        mine = make_conversation(self.user, self.friend, Conversation.Status.ACCEPTED, first_body="hi")
        third = make_account(email="third@example.com", username="third_one")
        theirs = make_conversation(third, self.user, Conversation.Status.PENDING, first_body="yo")
        unrelated = make_conversation(self.friend, third, Conversation.Status.ACCEPTED, first_body="keep")

        delete(self.client)

        self.assertFalse(Conversation.objects.filter(pk__in=[mine.pk, theirs.pk]).exists())
        self.assertEqual(list(Message.objects.values_list("body", flat=True)), ["keep"])
        self.assertTrue(Conversation.objects.filter(pk=unrelated.pk).exists())

    @unittest.skipUnless(MODERATION, "приложение moderation подключается ветками B9")
    def test_blocks_are_deleted_in_both_directions(self):
        from apps.moderation.models import Block

        Block.objects.create(blocker=self.user, blocked=self.friend)
        Block.objects.create(blocker=self.friend, blocked=self.user)

        delete(self.client)

        self.assertFalse(Block.objects.exists())

    @unittest.skipUnless(MODERATION, "приложение moderation подключается ветками B9")
    def test_reports_by_the_user_stay_without_an_author_and_reports_on_the_user_are_deleted(self):
        from apps.moderation.models import Report

        made = Report.objects.create(reporter=self.user, target=self.friend, reason="spam")
        received = Report.objects.create(reporter=self.friend, target=self.user, reason="spam")

        delete(self.client)

        made.refresh_from_db()
        self.assertIsNone(made.reporter)
        self.assertFalse(Report.objects.filter(pk=received.pk).exists())


@override_settings(THROTTLING_ENABLED=True)
class DeleteThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = make_account(email="jane@example.com", username="janedoe")
        self.client.force_login(self.user)

    def test_11th_attempt_in_an_hour_is_throttled(self):
        for _ in range(10):
            self.assertEqual(delete(self.client, "Wrong-pass-9911!").status_code, 400)

        response = delete(self.client)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(error_of(response)["code"], "throttled")
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_other_methods_of_me_are_not_limited_by_it(self):
        for _ in range(10):
            delete(self.client, "Wrong-pass-9911!")

        self.assertEqual(self.client.get(ME).status_code, 200)
