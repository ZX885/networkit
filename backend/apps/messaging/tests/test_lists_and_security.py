import logging
from datetime import timedelta
from unittest import mock

from django.contrib.admin.models import LogEntry
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.messaging.models import Conversation, Message
from apps.profiles.tests.factories import make_user
from apps.users.models import User
from apps.users.tests.helpers import error_of, make_account

from .helpers import (
    CONVERSATION_KEYS,
    CONVERSATIONS,
    LAST_MESSAGE_KEYS,
    OTHER_USER_KEYS,
    add_message,
    make_conversation,
    person,
    url,
)

Status = Conversation.Status


class ListTestCase(APITestCase):
    def setUp(self):
        self.me = person("me_user")
        self.client.force_login(self.me)

    def box(self, name=None, **params):
        if name:
            params["box"] = name
        return self.client.get(CONVERSATIONS, params)

    def usernames(self, name=None):
        return [item["other_user"]["username"] for item in self.box(name).json()["results"]]


class BoxTests(ListTestCase):
    def setUp(self):
        super().setUp()
        self.accepted = make_conversation(self.me, person("accepted_one"), Status.ACCEPTED)
        self.incoming = make_conversation(person("incoming_one"), self.me, Status.PENDING)
        self.sent = make_conversation(self.me, person("sent_one"), Status.PENDING)
        self.sent_declined = make_conversation(self.me, person("declined_one"), Status.DECLINED)
        self.i_declined = make_conversation(person("refused_one"), self.me, Status.DECLINED)

    def test_default_box_is_chats(self):
        self.assertEqual(self.usernames(), ["accepted_one"])
        self.assertEqual(self.usernames("chats"), ["accepted_one"])

    def test_requests_are_incoming_pending_only(self):
        self.assertEqual(self.usernames("requests"), ["incoming_one"])

    def test_sent_shows_my_pending_and_declined_as_pending(self):
        results = self.box("sent").json()["results"]

        self.assertEqual({r["other_user"]["username"] for r in results}, {"sent_one", "declined_one"})
        self.assertEqual({r["status"] for r in results}, {"pending"})
        self.assertTrue(all(r["initiated_by_me"] for r in results))

    def test_what_i_declined_is_in_no_box(self):
        for name in ("chats", "requests", "sent"):
            self.assertNotIn("refused_one", self.usernames(name))

    def test_unknown_box_is_400(self):
        self.assertEqual(self.box("everything").status_code, 400)

    def test_ordering_is_newest_activity_first(self):
        now = timezone.now()
        other = person("older_chat")
        old = make_conversation(self.me, other, Status.ACCEPTED)
        Conversation.objects.filter(pk=old.pk).update(last_message_at=now - timedelta(days=5))
        Conversation.objects.filter(pk=self.accepted.pk).update(last_message_at=now)

        self.assertEqual(self.usernames("chats"), ["accepted_one", "older_chat"])

    def test_pagination(self):
        for i in range(13):
            make_conversation(self.me, person(f"chat{i}"), Status.ACCEPTED)

        first = self.box("chats").json()
        second = self.box("chats", page=2).json()

        self.assertEqual(set(first), {"count", "next", "previous", "results"})
        self.assertEqual((first["count"], len(first["results"])), (14, 12))
        self.assertEqual(len(second["results"]), 2)
        self.assertEqual(len(self.box("chats", page_size=1000).json()["results"]), 14)

    def test_hidden_partners_are_not_listed(self):
        banned = person("banned_one")
        make_conversation(self.me, banned, Status.ACCEPTED)
        User.objects.filter(pk=banned.pk).update(is_banned=True)
        inactive = person("inactive_one")
        make_conversation(self.me, inactive, Status.ACCEPTED)
        User.objects.filter(pk=inactive.pk).update(is_active=False)

        self.assertEqual(self.usernames("chats"), ["accepted_one"])

    def test_other_peoples_conversations_are_not_listed(self):
        make_conversation(person("x_one"), person("y_one"), Status.ACCEPTED)

        self.assertEqual(self.usernames("chats"), ["accepted_one"])

    def test_requires_login(self):
        self.client.logout()

        self.assertEqual(self.box().status_code, 401)


class ItemContentTests(ListTestCase):
    def test_exact_keys_content_and_unread(self):
        other = person("maria", field="design", date_of_birth=None) if False else person("maria", field="design")
        conversation = make_conversation(other, self.me, Status.ACCEPTED, first_body="first")
        add_message(conversation, self.me, "my answer", seen=True)
        add_message(conversation, other, "unread one")
        add_message(conversation, other, "unread two")

        item = self.box("chats").json()["results"][0]
        raw = self.box("chats").content.decode()

        self.assertEqual(set(item), CONVERSATION_KEYS)
        self.assertEqual(set(item["other_user"]), OTHER_USER_KEYS)
        self.assertEqual(set(item["last_message"]), LAST_MESSAGE_KEYS)
        self.assertEqual(item["other_user"]["username"], "maria")
        self.assertEqual(item["other_user"]["field_label"], "Design")
        self.assertIsNone(item["other_user"]["avatar_url"])
        self.assertEqual(item["last_message"]["body"], "unread two")
        self.assertFalse(item["last_message"]["sender_is_me"])
        self.assertEqual((item["unread_count"], item["status"], item["initiated_by_me"]), (3, "accepted", False))
        self.assertEqual(item["id"], str(conversation.pk))
        for forbidden in ("email", "date_of_birth", "example.com", "gender", "is_banned", "phone", "school"):
            self.assertNotIn(forbidden, raw)

    def test_requests_do_not_have_unread_counts(self):
        make_conversation(person("maria"), self.me, Status.PENDING)

        self.assertEqual(self.box("requests").json()["results"][0]["unread_count"], 0)

    def test_name_comes_from_the_visibility_function(self):
        other = person("maria", first_name="Maria", last_name="Stone")
        make_conversation(other, self.me, Status.ACCEPTED)
        with mock.patch(
            "apps.messaging.serializers.ProfileVisibility.name",
            return_value={"first_name": "M.", "last_name": "S."},
        ):
            item = self.box("chats").json()["results"][0]

        self.assertEqual((item["other_user"]["first_name"], item["other_user"]["last_name"]), ("M.", "S."))

    def test_detail_has_the_same_shape(self):
        conversation = make_conversation(person("maria"), self.me, Status.PENDING)

        data = self.client.get(url(conversation)).json()

        self.assertEqual(set(data), CONVERSATION_KEYS)
        self.assertEqual(data["last_message"]["body"], "Hello!")


class SummaryTests(ListTestCase):
    def test_counts(self):
        accepted = make_conversation(person("accepted_one"), self.me, Status.ACCEPTED, first_body=None)
        add_message(accepted, accepted.initiator, "u1")
        add_message(accepted, accepted.initiator, "u2")
        add_message(accepted, self.me, "mine")
        add_message(accepted, accepted.initiator, "read", seen=True)
        make_conversation(person("incoming_one"), self.me, Status.PENDING)  # запрос, его сообщение не «непрочитанное»
        make_conversation(person("incoming_two"), self.me, Status.PENDING)
        make_conversation(self.me, person("sent_one"), Status.PENDING)  # исходящий не считается
        make_conversation(person("refused_one"), self.me, Status.DECLINED)

        data = self.client.get(f"{CONVERSATIONS}summary/").json()

        self.assertEqual(data, {"unread_messages": 2, "pending_requests": 2})

    def test_zero_and_login_required(self):
        self.assertEqual(self.client.get(f"{CONVERSATIONS}summary/").json(), {"unread_messages": 0, "pending_requests": 0})
        self.client.logout()
        self.assertEqual(self.client.get(f"{CONVERSATIONS}summary/").status_code, 401)

    def test_banned_partner_is_not_counted(self):
        banned = person("banned_one")
        make_conversation(banned, self.me, Status.PENDING)
        User.objects.filter(pk=banned.pk).update(is_banned=True)

        self.assertEqual(self.client.get(f"{CONVERSATIONS}summary/").json()["pending_requests"], 0)


class QueryCountTests(ListTestCase):
    def count(self, path, params=None):
        self.client.get(path, params)  # прогрев
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(path, params)
        self.assertEqual(response.status_code, 200)
        return len(queries)

    def fill(self, n, start=0):
        for i in range(start, start + n):
            other = person(f"chat{i}")
            conversation = make_conversation(other, self.me, Status.ACCEPTED, first_body="hi")
            add_message(conversation, other, "unread")

    def test_list_queries_do_not_grow_with_the_number_of_conversations(self):
        self.fill(2)
        small = self.count(CONVERSATIONS)
        self.fill(10, start=2)

        large = self.count(CONVERSATIONS)

        self.assertEqual(large, small)
        self.assertEqual(self.client.get(CONVERSATIONS).json()["count"], 12)

    def test_requests_box_and_summary_are_constant_too(self):
        for i in range(2):
            make_conversation(person(f"req{i}"), self.me, Status.PENDING)
        small = (self.count(CONVERSATIONS, {"box": "requests"}), self.count(f"{CONVERSATIONS}summary/"))
        for i in range(2, 12):
            make_conversation(person(f"req{i}"), self.me, Status.PENDING)

        large = (self.count(CONVERSATIONS, {"box": "requests"}), self.count(f"{CONVERSATIONS}summary/"))

        self.assertEqual(large, small)


class DatabaseTests(TestCase):
    def setUp(self):
        self.a, self.b = sorted([person("user_one"), person("user_two")], key=lambda u: u.pk)
        self.c = person("user_three")

    def test_pair_must_be_ordered(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Conversation.objects.create(user_a=self.b, user_b=self.a, initiator=self.a)

    def test_user_cannot_talk_to_himself(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Conversation.objects.create(user_a=self.a, user_b=self.a, initiator=self.a)

    def test_pair_is_unique(self):
        Conversation.objects.create(user_a=self.a, user_b=self.b, initiator=self.a)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Conversation.objects.create(user_a=self.a, user_b=self.b, initiator=self.b)

    def test_initiator_must_be_a_member(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Conversation.objects.create(user_a=self.a, user_b=self.b, initiator=self.c)

    def test_sender_outside_the_conversation_is_refused_by_the_service(self):
        from rest_framework.exceptions import NotFound

        from apps.messaging import services

        conversation = Conversation.objects.create(
            user_a=self.a, user_b=self.b, initiator=self.a, status=Status.ACCEPTED
        )

        with self.assertRaises(NotFound):
            services.send_message(conversation.pk, self.c, "intruder")
        self.assertFalse(Message.objects.exists())

    def test_deleting_a_user_removes_conversations_and_messages(self):
        conversation = make_conversation(self.a, self.b, Status.ACCEPTED)
        add_message(conversation, self.b, "reply")

        self.a.delete()

        self.assertEqual(Conversation.objects.count(), 0)
        self.assertEqual(Message.objects.count(), 0)
        self.assertTrue(User.objects.filter(pk=self.b.pk).exists())

    def test_deleting_the_other_user_also_removes_them(self):
        make_conversation(self.a, self.b, Status.ACCEPTED)

        self.b.delete()

        self.assertEqual(Conversation.objects.count(), 0)

    def test_conversation_ids_are_uuids(self):
        conversation = make_conversation(self.a, self.b)

        self.assertEqual(len(str(conversation.pk)), 36)


SECRET = "SECRET-BODY-8f3a9c"


class NoBodiesInLogsTests(APITestCase):
    """Тело сообщения не должно попадать в логи и трейсбеки, даже если ошибка содержит его текст."""

    def setUp(self):
        self.me = person("me_user")
        self.other = person("maria")
        self.conversation = make_conversation(self.other, self.me, Status.ACCEPTED)
        self.client.force_login(self.me)

    def logged_text(self, logs):
        formatter = logging.Formatter()
        return "\n".join(formatter.format(record) for record in logs.records)

    def post_with_error(self, error):
        with mock.patch("apps.messaging.views.services.send_message", side_effect=error):
            with self.assertLogs(level="ERROR") as logs:
                response = self.client.post(url(self.conversation, "messages/"), {"body": SECRET}, format="json")
        return response, self.logged_text(logs)

    def test_error_text_containing_the_body_is_not_logged(self):
        response, logged = self.post_with_error(RuntimeError(f"could not store {SECRET}"))

        self.assertEqual(response.status_code, 500)
        self.assertEqual(error_of(response), {"code": "server_error", "message": "Something went wrong."})
        self.assertNotIn(SECRET, response.content.decode())
        self.assertNotIn(SECRET, logged)
        self.assertIn("RedactedError", logged)  # в логе остаётся тип ошибки и место в коде
        self.assertIn("RuntimeError", logged)

    def test_chained_database_error_with_the_row_is_not_logged(self):
        def boom(*args, **kwargs):
            try:
                raise ValueError(f"cause: {SECRET}")
            except ValueError as cause:
                raise IntegrityError(f'DETAIL: Failing row contains (1, 2, {SECRET}, now)') from cause

        response, logged = self.post_with_error(boom)

        self.assertEqual(response.status_code, 500)
        self.assertNotIn(SECRET, logged)
        # текст самой ошибки («IntegrityError: DETAIL: …») в лог не попадает; строка кода теста в
        # трейсбеке — это исходный код, а не данные
        self.assertNotIn("IntegrityError: DETAIL", logged)

    def test_creating_a_request_with_a_failure_does_not_log_the_body_either(self):
        with mock.patch("apps.messaging.views.services.create_request", side_effect=DatabaseError(SECRET)):
            with self.assertLogs(level="ERROR") as logs:
                response = self.client.post(CONVERSATIONS, {"username": "maria", "body": SECRET}, format="json")

        self.assertEqual(response.status_code, 500)
        self.assertNotIn(SECRET, self.logged_text(logs))
        self.assertNotIn(SECRET, response.content.decode())

    def test_other_paths_still_log_the_error_text(self):
        with mock.patch("apps.profiles.views.MeView.get", side_effect=RuntimeError("visible detail")):
            with self.assertLogs("config.exceptions", "ERROR") as logs:
                self.client.get("/api/me/")

        self.assertIn("visible detail", self.logged_text(logs))

    def test_successful_and_failed_requests_do_not_write_bodies_to_logs(self):
        with self.assertNoLogs("apps.messaging", "DEBUG"):
            self.client.post(url(self.conversation, "messages/"), {"body": SECRET}, format="json")
            self.client.post(url(self.conversation, "messages/"), {"body": ""}, format="json")


class AdminTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(email="owner@example.com", password="Passw0rd-xyz-1")
        self.staff = User.objects.create_user(email="staff@example.com", password="Passw0rd-xyz-1", is_staff=True)
        self.a, self.b = person("user_one"), person("user_two")
        self.conversation = make_conversation(self.a, self.b, Status.ACCEPTED, first_body="visible only to owners")
        self.message = Message.objects.first()

    def test_superuser_can_read_conversations_and_messages(self):
        self.client.force_login(self.superuser)

        index = self.client.get(reverse("admin:index")).content.decode()
        conv_list = self.client.get(reverse("admin:messaging_conversation_changelist"))
        msg_list = self.client.get(reverse("admin:messaging_message_changelist"))
        msg_card = self.client.get(reverse("admin:messaging_message_change", args=[self.message.pk]))

        self.assertIn("Messaging", index)
        self.assertEqual(conv_list.status_code, 200)
        self.assertEqual(msg_list.status_code, 200)
        self.assertNotIn("visible only to owners", msg_list.content.decode())  # в списке текста нет
        self.assertEqual(msg_card.status_code, 200)
        self.assertIn("visible only to owners", msg_card.content.decode())  # в карточке — виден

    def test_viewing_creates_no_log_entries(self):
        self.client.force_login(self.superuser)
        before = LogEntry.objects.count()

        self.client.get(reverse("admin:messaging_message_change", args=[self.message.pk]))
        self.client.get(reverse("admin:messaging_message_changelist"))

        self.assertEqual(LogEntry.objects.count(), before)

    def test_nothing_can_be_added_changed_or_deleted(self):
        self.client.force_login(self.superuser)

        for name in ("conversation", "message"):
            self.assertEqual(self.client.get(reverse(f"admin:messaging_{name}_add")).status_code, 403)
        change = reverse("admin:messaging_message_change", args=[self.message.pk])
        self.assertEqual(self.client.post(change, {"body": "changed"}).status_code, 403)
        delete = reverse("admin:messaging_message_delete", args=[self.message.pk])
        self.assertEqual(self.client.get(delete).status_code, 403)
        self.assertEqual(self.client.post(delete, {"post": "yes"}).status_code, 403)
        self.message.refresh_from_db()
        self.assertEqual(self.message.body, "visible only to owners")
        self.assertEqual(Message.objects.count(), 1)

    def test_ordinary_staff_does_not_see_the_module(self):
        self.client.force_login(self.staff)

        index = self.client.get(reverse("admin:index")).content.decode()

        self.assertNotIn("Messaging", index)
        for name in ("conversation", "message"):
            self.assertEqual(self.client.get(reverse(f"admin:messaging_{name}_changelist")).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("admin:messaging_message_change", args=[self.message.pk])).status_code, 403
        )

    def test_staff_with_explicit_permissions_still_cannot(self):
        from django.contrib.auth.models import Permission

        self.staff.user_permissions.set(Permission.objects.filter(content_type__app_label="messaging"))
        self.client.force_login(self.staff)

        self.assertEqual(self.client.get(reverse("admin:messaging_message_changelist")).status_code, 403)
        self.assertNotIn("Messaging", self.client.get(reverse("admin:index")).content.decode())

    def test_message_str_does_not_show_the_body(self):
        self.assertNotIn("visible only to owners", str(self.message))
        self.assertIsNotNone(make_user)
