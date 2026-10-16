from datetime import timedelta

from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.messaging.models import Conversation
from apps.messaging.tests.helpers import make_conversation
from apps.moderation.models import Block, Report
from apps.users.models import User

from .helpers import SECRET, person

PASSWORD = "Passw0rd-xyz-1"
LIST = "admin:moderation_report_changelist"


def make_report(reporter, target, reason="spam", status="open", **extra):
    return Report.objects.create(reporter=reporter, target=target, reason=reason, status=status, **extra)


class AdminBase(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(email="owner@example.com", password=PASSWORD)
        self.staff = User.objects.create_user(email="staff@example.com", password=PASSWORD, is_staff=True)
        self.reporter = person("reporter")
        self.target = person("target_one")

    def ids_in_list(self, **params):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse(LIST), params)
        self.assertEqual(response.status_code, 200)
        return [report.pk for report in response.context["cl"].result_list]


class ReportListTests(AdminBase):
    def test_urgent_reasons_first_then_newest_first_inside_a_group(self):
        now = timezone.now()
        other = person("other_one")
        old_urgent = make_report(self.reporter, self.target, "underage")
        new_spam = make_report(self.reporter, other, "spam")
        new_harassment = make_report(other, self.target, "harassment")
        newest_other = make_report(other, self.reporter, "other")
        for report, days in ((old_urgent, 5), (new_spam, 1), (new_harassment, 2), (newest_other, 0)):
            Report.objects.filter(pk=report.pk).update(created_at=now - timedelta(days=days))

        order = self.ids_in_list()

        # срочные: harassment (2 дня) новее underage (5 дней); затем остальные: other (0) новее spam (1)
        self.assertEqual(order, [new_harassment.pk, old_urgent.pk, newest_other.pk, new_spam.pk])

    def test_priority_filter(self):
        urgent = make_report(self.reporter, self.target, "underage")
        usual = make_report(self.reporter, person("other_one"), "spam")

        self.assertEqual(self.ids_in_list(priority="urgent"), [urgent.pk])
        self.assertEqual(self.ids_in_list(priority="other"), [usual.pk])

    def test_status_and_reason_filters(self):
        open_spam = make_report(self.reporter, self.target, "spam")
        done = make_report(person("xray1"), self.target, "spam", status="dismissed")

        self.assertEqual(self.ids_in_list(status__exact="dismissed"), [done.pk])
        self.assertEqual(sorted(self.ids_in_list(reason__exact="spam")), sorted([open_spam.pk, done.pk]))

    def test_list_shows_the_number_of_open_reports_on_the_same_person(self):
        make_report(self.reporter, self.target)
        make_report(person("xray1"), self.target)
        make_report(person("xray2"), self.target, status="dismissed")  # закрытая не считается
        self.client.force_login(self.superuser)

        response = self.client.get(reverse(LIST))

        counts = {r.pk: r.open_on_target_count for r in response.context["cl"].result_list}
        self.assertEqual(set(counts.values()), {2})

    def test_list_query_count_does_not_grow_with_reports(self):
        self.client.force_login(self.superuser)
        for number in range(3):
            make_report(person(f"reporter{number}"), self.target)
        with CaptureQueriesContext(connection) as few:
            self.client.get(reverse(LIST))

        for number in range(3, 15):
            make_report(person(f"reporter{number}"), person(f"target{number}"), "underage")
        with CaptureQueriesContext(connection) as many:
            self.client.get(reverse(LIST))

        self.assertEqual(len(few), len(many))


class ReportCardTests(AdminBase):
    def test_card_shows_open_count_and_other_reports_without_their_texts(self):
        one = make_report(self.reporter, self.target, "spam", details="MY OWN TEXT")
        make_report(person("xray1"), self.target, "harassment", details=SECRET)
        make_report(person("xray2"), self.target, "underage", status="dismissed", details=SECRET + "2")
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("admin:moderation_report_change", args=[one.pk]))
        page = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("MY OWN TEXT", page)  # текст самой жалобы виден
        self.assertNotIn(SECRET, page)  # чужие тексты — нет
        self.assertIn("harassment", page)
        self.assertIn("underage", page)
        self.assertIn("dismissed", page)
        self.assertEqual(response.context["adminform"].form.instance.open_on_target_count, 2)

    def test_card_links_to_the_conversation(self):
        conversation = make_conversation(self.reporter, self.target, Conversation.Status.ACCEPTED)
        report = make_report(self.reporter, self.target, conversation=conversation)
        self.client.force_login(self.superuser)

        page = self.client.get(reverse("admin:moderation_report_change", args=[report.pk])).content.decode()

        self.assertIn(reverse("admin:messaging_conversation_change", args=[conversation.pk]), page)

    def test_report_text_cannot_be_edited_only_status_and_note(self):
        report = make_report(self.reporter, self.target, "spam", details="original")
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("admin:moderation_report_change", args=[report.pk]),
            {"status": "dismissed", "staff_note": "not an issue", "details": "hacked", "reason": "other"},
        )

        report.refresh_from_db()
        self.assertEqual((report.details, report.reason), ("original", "spam"))
        self.assertEqual((report.status, report.staff_note), ("dismissed", "not an issue"))
        self.assertEqual(report.handled_by, self.superuser)
        self.assertIsNotNone(report.handled_at)

    def test_reopening_clears_the_handler(self):
        report = make_report(self.reporter, self.target, status="dismissed")
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("admin:moderation_report_change", args=[report.pk]),
            {"status": "open", "staff_note": ""},
        )

        report.refresh_from_db()
        self.assertEqual((report.status, report.handled_by, report.handled_at), ("open", None, None))

    def test_cannot_add_or_delete(self):
        report = make_report(self.reporter, self.target)
        self.client.force_login(self.superuser)

        self.assertEqual(self.client.get(reverse("admin:moderation_report_add")).status_code, 403)
        delete = reverse("admin:moderation_report_delete", args=[report.pk])
        self.assertEqual(self.client.post(delete, {"post": "yes"}).status_code, 403)
        self.assertTrue(Report.objects.filter(pk=report.pk).exists())


class ReportActionTests(AdminBase):
    def run_action(self, action, reports):
        self.client.force_login(self.superuser)
        return self.client.post(
            reverse(LIST),
            {"action": action, "_selected_action": [r.pk for r in reports]},
            follow=True,
        )

    def test_mark_dismissed_and_actioned(self):
        first = make_report(self.reporter, self.target)
        second = make_report(person("xray1"), self.target)

        self.run_action("mark_dismissed", [first])
        self.run_action("mark_actioned", [second])

        first.refresh_from_db(), second.refresh_from_db()
        self.assertEqual((first.status, first.handled_by), ("dismissed", self.superuser))
        self.assertEqual((second.status, second.handled_by), ("actioned", self.superuser))
        self.assertIsNotNone(second.handled_at)

    def test_ban_target_bans_ends_sessions_and_marks_actioned(self):
        report = make_report(self.reporter, self.target)
        other_report = make_report(self.reporter, person("calm"))
        Client().force_login(self.target)  # живая сессия цели (отдельный клиент)
        self.assertEqual(Session.objects.count(), 1)

        self.run_action("ban_target_users", [report])

        self.target.refresh_from_db()
        report.refresh_from_db(), other_report.refresh_from_db()
        self.assertTrue(self.target.is_banned)
        self.assertIsNotNone(self.target.banned_at)
        self.assertEqual(report.status, "actioned")
        self.assertEqual(report.handled_by, self.superuser)
        self.assertEqual(other_report.status, "open")
        keys = [s.get_decoded().get("_auth_user_id") for s in Session.objects.all()]
        self.assertNotIn(str(self.target.pk), keys)

    def test_ban_action_does_not_ban_superusers(self):
        boss = User.objects.create_superuser(email="boss@example.com", password=PASSWORD)
        report = make_report(self.reporter, boss)

        self.run_action("ban_target_users", [report])

        boss.refresh_from_db()
        self.assertFalse(boss.is_banned)


class AdminAccessTests(AdminBase):
    def test_ordinary_staff_has_no_access_to_reports_and_blocks(self):
        report = make_report(self.reporter, self.target)
        Block.objects.create(blocker=self.reporter, blocked=self.target)
        self.client.force_login(self.staff)

        index = self.client.get(reverse("admin:index")).content.decode()

        self.assertNotIn("Moderation", index)
        for name in ("moderation_report_changelist", "moderation_block_changelist"):
            self.assertEqual(self.client.get(reverse(f"admin:{name}")).status_code, 403)
        change = reverse("admin:moderation_report_change", args=[report.pk])
        self.assertEqual(self.client.get(change).status_code, 403)
        self.assertEqual(self.client.post(change, {"status": "dismissed"}).status_code, 403)
        report.refresh_from_db()
        self.assertEqual(report.status, "open")

    def test_staff_with_explicit_permissions_still_cannot(self):
        from django.contrib.auth.models import Permission

        self.staff.user_permissions.set(Permission.objects.filter(content_type__app_label="moderation"))
        self.client.force_login(self.staff)

        self.assertEqual(self.client.get(reverse(LIST)).status_code, 403)

    def test_staff_cannot_run_actions(self):
        report = make_report(self.reporter, self.target)
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse(LIST), {"action": "ban_target_users", "_selected_action": [report.pk]}
        )

        self.assertEqual(response.status_code, 403)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_banned)

    def test_blocks_are_read_only_for_the_superuser(self):
        block = Block.objects.create(blocker=self.reporter, blocked=self.target)
        self.client.force_login(self.superuser)

        listing = self.client.get(reverse("admin:moderation_block_changelist"))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:moderation_block_add")).status_code, 403)
        delete = reverse("admin:moderation_block_delete", args=[block.pk])
        self.assertEqual(self.client.post(delete, {"post": "yes"}).status_code, 403)
        self.assertEqual(Block.objects.count(), 1)

    def test_viewing_reports_creates_no_log_entries(self):
        report = make_report(self.reporter, self.target)
        self.client.force_login(self.superuser)
        before = LogEntry.objects.count()

        self.client.get(reverse(LIST))
        self.client.get(reverse("admin:moderation_report_change", args=[report.pk]))

        self.assertEqual(LogEntry.objects.count(), before)


class UserAdminOpenReportsTests(AdminBase):
    def test_users_list_has_open_reports_column(self):
        make_report(self.reporter, self.target)
        make_report(person("xray1"), self.target)
        make_report(person("xray2"), self.target, status="actioned")
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("admin:users_user_changelist"))

        counts = {u.email: u.open_reports_count for u in response.context["cl"].result_list}
        self.assertEqual(counts[self.target.email], 2)
        self.assertEqual(counts[self.reporter.email], 0)
        self.assertIn("Open reports", response.content.decode())

    def test_users_list_query_count_does_not_grow_with_users_and_reports(self):
        self.client.force_login(self.superuser)
        make_report(self.reporter, self.target)
        with CaptureQueriesContext(connection) as few:
            self.client.get(reverse("admin:users_user_changelist"))

        for number in range(12):
            user = person(f"userx{number}")
            make_report(self.reporter, user)
            make_report(person(f"voter{number}"), user)
        with CaptureQueriesContext(connection) as many:
            self.client.get(reverse("admin:users_user_changelist"))

        self.assertEqual(len(few), len(many))

    def test_column_is_sortable(self):
        make_report(self.reporter, self.target)
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("admin:users_user_changelist"), {"o": "-5"})

        self.assertEqual(response.status_code, 200)
