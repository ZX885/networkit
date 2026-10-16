import logging
from unittest import mock

from django.core.cache import cache
from django.db import DatabaseError, IntegrityError, transaction
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.messaging.models import Conversation
from apps.messaging.tests.helpers import make_conversation
from apps.moderation.models import Report
from apps.profiles.tests.factories import make_user
from apps.users.tests.helpers import error_of, field_codes

from .helpers import REPORTS, SECRET, block, person

Status = Conversation.Status


def report(client, username="maria", reason="spam", **extra):
    return client.post(REPORTS, {"username": username, "reason": reason, **extra}, format="json")


class CreateReportTests(APITestCase):
    def setUp(self):
        self.me = person("me_user")
        self.maria = person("maria")
        self.client.force_login(self.me)

    def test_report_is_received(self):
        response = report(self.client, details="  sells things  ")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"status": "received"})
        saved = Report.objects.get()
        self.assertEqual((saved.reporter, saved.target, saved.reason), (self.me, self.maria, "spam"))
        self.assertEqual((saved.details, saved.status, saved.conversation), ("sells things", "open", None))

    def test_duplicate_open_report_is_201_and_creates_nothing(self):
        first = report(self.client)
        second = report(self.client, reason="harassment", details="again")

        self.assertEqual((first.status_code, second.status_code), (201, 201))
        self.assertEqual(first.json(), second.json())
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(Report.objects.get().reason, "spam")

    def test_new_report_is_possible_after_the_old_one_was_handled(self):
        report(self.client)
        Report.objects.update(status=Report.Status.DISMISSED)

        self.assertEqual(report(self.client).status_code, 201)

        self.assertEqual(Report.objects.count(), 2)

    def test_report_on_yourself_is_rejected(self):
        response = report(self.client, username="me_user")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_of(response)["code"], "cannot_target_self")
        self.assertFalse(Report.objects.exists())

    def test_unknown_person_is_404(self):
        self.assertEqual(report(self.client, username="nobody").status_code, 404)
        self.assertEqual(report(self.client, username="").status_code, 404)

    def test_reason_must_be_from_the_list(self):
        bad = report(self.client, reason="because")
        missing = self.client.post(REPORTS, {"username": "maria"}, format="json")

        self.assertEqual(bad.status_code, 400)
        self.assertEqual(field_codes(bad, "reason"), ["invalid_choice"])
        self.assertEqual(field_codes(missing, "reason"), ["required"])
        self.assertFalse(Report.objects.exists())

    def test_every_reason_from_meta_is_accepted(self):
        reasons = self.client.get("/api/meta/").json()["report_reasons"]

        for number, item in enumerate(reasons):
            with self.subTest(item["code"]):
                other = person(f"target{number}")
                self.assertEqual(report(self.client, other.profile.username, item["code"]).status_code, 201)
        self.assertEqual(Report.objects.count(), len(reasons))

    def test_details_are_limited_to_1000_characters(self):
        too_long = report(self.client, details="x" * 1001)
        exact = report(self.client, details="x" * 1000)

        self.assertEqual(too_long.status_code, 400)
        self.assertEqual(field_codes(too_long, "details"), ["too_long"])
        self.assertEqual(exact.status_code, 201)

    def test_details_must_be_text(self):
        response = report(self.client, details=["a"])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "details"), ["invalid"])

    def test_body_must_be_an_object(self):
        response = self.client.post(REPORTS, ["maria"], format="json")

        self.assertEqual(response.status_code, 400)  # причина не указана

    def test_anonymous_cannot_report(self):
        self.client.logout()

        self.assertIn(report(self.client).status_code, (401, 403))

    def test_blocked_or_blocking_person_can_still_be_reported(self):
        block(self.maria, self.me)

        self.assertEqual(report(self.client).status_code, 201)  # ответ не выдаёт блокировку

    def test_response_is_the_same_for_new_and_duplicate_reports(self):
        first = report(self.client)
        second = report(self.client)

        self.assertEqual(first.content, second.content)


class ConversationReportTests(APITestCase):
    def setUp(self):
        self.me = person("me_user")
        self.maria = person("maria")
        self.conversation = make_conversation(self.maria, self.me, Status.ACCEPTED, first_body=SECRET)
        self.client.force_login(self.me)

    def test_report_on_a_conversation_links_it_without_copying_text(self):
        response = report(self.client, conversation_id=str(self.conversation.pk), details="rude")

        self.assertEqual(response.status_code, 201)
        saved = Report.objects.get()
        self.assertEqual(saved.conversation, self.conversation)
        self.assertNotIn(SECRET, saved.details)

    def test_duplicate_report_adds_the_conversation_link(self):
        report(self.client)
        self.assertIsNone(Report.objects.get().conversation)

        report(self.client, conversation_id=str(self.conversation.pk))

        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(Report.objects.get().conversation, self.conversation)

    def test_someone_elses_conversation_is_404(self):
        other_a, other_b = person("other_a"), person("other_b")
        foreign = make_conversation(other_a, other_b, Status.ACCEPTED)

        response = report(self.client, username="other_a", conversation_id=str(foreign.pk))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Report.objects.exists())

    def test_conversation_with_another_person_is_404(self):
        carol = person("carol")

        response = report(self.client, username="carol", conversation_id=str(self.conversation.pk))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(carol.profile.username, "carol")
        self.assertFalse(Report.objects.exists())

    def test_bad_or_unknown_conversation_id_is_404(self):
        for value in ("not-a-uuid", "00000000-0000-0000-0000-000000000000", 5):
            with self.subTest(value):
                self.assertEqual(report(self.client, conversation_id=value).status_code, 404)

    def test_report_on_a_conversation_hidden_by_my_block_is_possible(self):
        block(self.me, self.maria)

        response = report(self.client, conversation_id=str(self.conversation.pk))

        self.assertEqual(response.status_code, 201)

    def test_deleting_the_conversation_keeps_the_report(self):
        report(self.client, conversation_id=str(self.conversation.pk))

        self.conversation.delete()

        saved = Report.objects.get()
        self.assertIsNone(saved.conversation)


@override_settings(THROTTLING_ENABLED=True)
class ReportThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.me = person("me_user")
        self.client.force_login(self.me)

    def test_11th_report_in_a_day_is_throttled(self):
        for number in range(10):
            person(f"target{number}")
            self.assertEqual(report(self.client, f"target{number}").status_code, 201)

        response = report(self.client, "target0")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(error_of(response)["code"], "throttled")


class ReportDatabaseTests(APITestCase):
    def test_self_report_is_rejected_by_the_database(self):
        user = make_user()

        with self.assertRaises(IntegrityError), transaction.atomic():
            Report.objects.create(reporter=user, target=user, reason="spam")

    def test_second_open_report_is_rejected_but_handled_ones_are_fine(self):
        a, b = make_user(), make_user()
        Report.objects.create(reporter=a, target=b, reason="spam", status="dismissed")
        Report.objects.create(reporter=a, target=b, reason="spam", status="actioned")
        Report.objects.create(reporter=a, target=b, reason="spam")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Report.objects.create(reporter=a, target=b, reason="other")

    def test_deleting_the_target_deletes_reports_but_the_reporter_only_clears_the_link(self):
        reporter, target = make_user(), make_user()
        Report.objects.create(reporter=reporter, target=target, reason="spam")

        reporter.delete()
        self.assertEqual(Report.objects.get().reporter, None)
        target.delete()
        self.assertFalse(Report.objects.exists())


class MetaTests(APITestCase):
    def test_meta_has_reasons_and_limits(self):
        data = self.client.get("/api/meta/").json()

        self.assertEqual(
            [item["code"] for item in data["report_reasons"]],
            ["fake_profile", "spam", "inappropriate", "harassment", "underage", "other"],
        )
        self.assertTrue(all(item["label"] for item in data["report_reasons"]))
        self.assertEqual(data["limits"]["details_max"], 1000)
        self.assertEqual(data["limits"]["blocks_max"], 200)


class PrivacyInLogsTests(APITestCase):
    """Текст жалобы и сообщений не попадает в логи и трейсбеки."""

    def setUp(self):
        self.me = person("me_user")
        person("maria")
        self.client.force_login(self.me)

    def logged_text(self, logs):
        formatter = logging.Formatter()
        return "\n".join(formatter.format(record) for record in logs.records)

    def test_report_failure_does_not_log_the_text(self):
        with mock.patch(
            "apps.moderation.views.services.create_report",
            side_effect=DatabaseError(f"Failing row contains ({SECRET})"),
        ):
            with self.assertLogs(level="ERROR") as logs:
                response = report(self.client, details=SECRET)

        self.assertEqual(response.status_code, 500)
        self.assertNotIn(SECRET, self.logged_text(logs))
        self.assertNotIn(SECRET, response.content.decode())
        self.assertIn("RedactedError", self.logged_text(logs))

    def test_block_failure_does_not_log_error_text(self):
        with mock.patch(
            "apps.moderation.views.services.block_user", side_effect=RuntimeError(f"oops {SECRET}")
        ):
            with self.assertLogs(level="ERROR") as logs:
                response = self.client.put("/api/blocks/maria/")

        self.assertEqual(response.status_code, 500)
        self.assertNotIn(SECRET, self.logged_text(logs))

    def test_successful_report_writes_nothing_with_the_text(self):
        with self.assertNoLogs("apps.moderation", "DEBUG"):
            report(self.client, details=SECRET)
            report(self.client, reason="bad")
