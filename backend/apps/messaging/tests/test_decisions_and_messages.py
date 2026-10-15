from django.test import override_settings
from rest_framework.test import APITestCase

from apps.messaging.models import Conversation, Message
from apps.users.models import User
from apps.users.tests.helpers import error_of, field_codes

from .helpers import (
    CONVERSATION_KEYS,
    CONVERSATIONS,
    MESSAGE_KEYS,
    add_message,
    make_conversation,
    person,
    url,
)

Status = Conversation.Status


class DecisionTestCase(APITestCase):
    def setUp(self):
        self.me = person("me_user")
        self.other = person("maria")
        self.third = person("stranger")


class AcceptDeclineTests(DecisionTestCase):
    def test_recipient_accepts_a_pending_request(self):
        conversation = make_conversation(self.other, self.me)
        self.client.force_login(self.me)

        response = self.client.post(url(conversation, "accept/"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), CONVERSATION_KEYS)
        self.assertEqual(response.json()["status"], "accepted")
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, Status.ACCEPTED)
        self.assertIsNotNone(conversation.decided_at)

    def test_recipient_declines_a_pending_request(self):
        conversation = make_conversation(self.other, self.me)
        self.client.force_login(self.me)

        response = self.client.post(url(conversation, "decline/"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "declined")  # получатель знает своё решение
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, Status.DECLINED)
        self.assertIsNotNone(conversation.decided_at)

    def test_initiator_cannot_accept_or_decline_whatever_the_state(self):
        self.client.force_login(self.me)
        for status in (Status.PENDING, Status.ACCEPTED, Status.DECLINED):
            with self.subTest(status):
                Conversation.objects.all().delete()
                conversation = make_conversation(self.me, self.other, status)
                for action in ("accept/", "decline/"):
                    response = self.client.post(url(conversation, action))
                    self.assertEqual(response.status_code, 409)
                    self.assertEqual(error_of(response)["code"], "invalid_state")
                conversation.refresh_from_db()
                self.assertEqual(conversation.status, status)

    def test_decision_only_from_pending(self):
        self.client.force_login(self.me)
        for status in (Status.ACCEPTED, Status.DECLINED):
            with self.subTest(status):
                Conversation.objects.all().delete()
                conversation = make_conversation(self.other, self.me, status)
                for action in ("accept/", "decline/"):
                    response = self.client.post(url(conversation, action))
                    self.assertEqual(response.status_code, 409)
                    self.assertEqual(error_of(response)["code"], "invalid_state")

    def test_decision_is_final(self):
        conversation = make_conversation(self.other, self.me)
        self.client.force_login(self.me)
        self.client.post(url(conversation, "decline/"))

        response = self.client.post(url(conversation, "accept/"))

        self.assertEqual(response.status_code, 409)

    def test_a_stranger_gets_404(self):
        conversation = make_conversation(self.other, self.me)
        self.client.force_login(self.third)

        for action in ("accept/", "decline/", ""):
            method = self.client.get if action == "" else self.client.post
            self.assertEqual(method(url(conversation, action)).status_code, 404)

    def test_unknown_or_malformed_id_is_404(self):
        self.client.force_login(self.me)

        self.assertEqual(self.client.get(f"{CONVERSATIONS}00000000-0000-0000-0000-000000000000/").status_code, 404)
        self.assertEqual(self.client.get(f"{CONVERSATIONS}not-a-uuid/").status_code, 404)

    def test_requires_login_and_only_post(self):
        conversation = make_conversation(self.other, self.me)

        self.assertEqual(self.client.post(url(conversation, "accept/")).status_code, 401)
        self.client.force_login(self.me)
        self.assertEqual(self.client.get(url(conversation, "accept/")).status_code, 405)


class MaskingTests(DecisionTestCase):
    """Отказ инициатору не сообщается: для него declined неотличим от pending."""

    def setUp(self):
        super().setUp()
        self.conversation = make_conversation(self.me, self.other, Status.DECLINED)
        self.client.force_login(self.me)

    def test_card_shows_pending(self):
        response = self.client.get(url(self.conversation))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "pending")
        self.assertTrue(response.json()["initiated_by_me"])
        self.assertNotIn("declined", response.content.decode())

    def test_sent_box_shows_pending(self):
        results = self.client.get(CONVERSATIONS, {"box": "sent"}).json()["results"]

        self.assertEqual([item["status"] for item in results], ["pending"])
        self.assertNotIn("declined", self.client.get(CONVERSATIONS, {"box": "sent"}).content.decode())

    def test_sending_a_message_gives_the_same_error_as_pending(self):
        declined = self.client.post(url(self.conversation, "messages/"), {"body": "hello?"}, format="json")
        pending_conversation = make_conversation(self.me, self.third, Status.PENDING)
        pending = self.client.post(url(pending_conversation, "messages/"), {"body": "hello?"}, format="json")

        self.assertEqual(declined.status_code, 409)
        self.assertEqual(error_of(declined)["code"], "request_pending")
        self.assertEqual(error_of(declined), error_of(pending))
        self.assertEqual(declined.status_code, pending.status_code)

    def test_decliner_does_not_see_it_in_requests_any_more_but_can_open_it(self):
        self.client.force_login(self.other)

        for box in ("chats", "requests", "sent"):
            self.assertEqual(self.client.get(CONVERSATIONS, {"box": box}).json()["count"], 0, box)
        self.assertEqual(self.client.get(url(self.conversation)).json()["status"], "declined")

    def test_summary_does_not_leak_a_decline(self):
        self.assertEqual(self.client.get(f"{CONVERSATIONS}summary/").json(), {"unread_messages": 0, "pending_requests": 0})


class SendMessageTests(DecisionTestCase):
    def post(self, conversation, body="hello"):
        return self.client.post(url(conversation, "messages/"), {"body": body}, format="json")

    def test_accepted_both_can_write_and_last_message_at_is_updated(self):
        conversation = make_conversation(self.other, self.me, Status.ACCEPTED)
        before = Conversation.objects.get(pk=conversation.pk).last_message_at
        for user in (self.me, self.other):
            self.client.force_login(user)
            response = self.post(conversation, f"from {user.profile.username}")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(set(response.json()), MESSAGE_KEYS)
            self.assertTrue(response.json()["sender_is_me"])
        conversation.refresh_from_db()
        self.assertGreater(conversation.last_message_at, before)
        self.assertEqual(conversation.last_message_at, Message.objects.order_by("-id").first().created_at)

    def test_pending_recipient_gets_accept_required(self):
        conversation = make_conversation(self.other, self.me, Status.PENDING)
        self.client.force_login(self.me)

        response = self.post(conversation)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(error_of(response)["code"], "accept_required")
        self.assertEqual(Message.objects.filter(conversation=conversation).count(), 1)

    def test_pending_initiator_gets_request_pending(self):
        conversation = make_conversation(self.me, self.other, Status.PENDING)
        self.client.force_login(self.me)

        response = self.post(conversation)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(error_of(response)["code"], "request_pending")

    def test_declined_recipient_gets_a_neutral_conversation_closed(self):
        conversation = make_conversation(self.other, self.me, Status.DECLINED)
        self.client.force_login(self.me)

        response = self.post(conversation)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(error_of(response)["code"], "conversation_closed")
        self.assertEqual(error_of(response)["message"], "You can't send messages to this user.")

    def test_body_validation(self):
        conversation = make_conversation(self.other, self.me, Status.ACCEPTED)
        self.client.force_login(self.me)

        for body, code in (("", "required"), ("  \r\n ", "required"), ("x" * 4001, "too_long")):
            with self.subTest(body[:4]):
                response = self.post(conversation, body)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(field_codes(response, "body"), [code])
        self.assertEqual(self.post(conversation, "x" * 4000).status_code, 201)
        self.assertEqual(self.client.post(url(conversation, "messages/"), {}, format="json").status_code, 400)

    def test_text_is_normalized_not_sanitized(self):
        conversation = make_conversation(self.other, self.me, Status.ACCEPTED)
        self.client.force_login(self.me)

        response = self.post(conversation, "  a\r\nb <script>x</script>  ")

        self.assertEqual(response.json()["body"], "a\nb <script>x</script>")

    def test_stranger_gets_404(self):
        conversation = make_conversation(self.other, self.me, Status.ACCEPTED)
        self.client.force_login(self.third)

        self.assertEqual(self.post(conversation).status_code, 404)
        self.assertEqual(self.client.get(url(conversation, "messages/")).status_code, 404)
        self.assertEqual(self.client.post(url(conversation, "read/")).status_code, 404)

    def test_banned_partner_hides_the_conversation(self):
        conversation = make_conversation(self.other, self.me, Status.ACCEPTED)
        self.client.force_login(self.me)
        User.objects.filter(pk=self.other.pk).update(is_banned=True)

        self.assertEqual(self.post(conversation).status_code, 404)
        self.assertEqual(self.client.get(url(conversation)).status_code, 404)
        self.assertEqual(self.client.get(CONVERSATIONS).json()["count"], 0)
        self.assertEqual(Message.objects.filter(conversation=conversation).count(), 1)  # сообщения сохраняются

    def test_requires_login(self):
        conversation = make_conversation(self.other, self.me, Status.ACCEPTED)

        self.assertEqual(self.client.post(url(conversation, "messages/"), {"body": "x"}, format="json").status_code, 401)
        self.assertEqual(self.client.get(url(conversation, "messages/")).status_code, 401)


class CursorTests(DecisionTestCase):
    def setUp(self):
        super().setUp()
        self.conversation = make_conversation(self.other, self.me, Status.ACCEPTED, first_body=None)
        self.ids = [add_message(self.conversation, self.other if i % 2 else self.me, f"m{i}").pk for i in range(60)]
        self.client.force_login(self.me)

    def get(self, **params):
        return self.client.get(url(self.conversation, "messages/"), params)

    def test_default_returns_the_latest_30_ascending(self):
        data = self.get().json()

        self.assertEqual(set(data), {"results", "has_more_older"})
        self.assertEqual([m["id"] for m in data["results"]], self.ids[-30:])
        self.assertTrue(data["has_more_older"])
        for message in data["results"]:
            self.assertEqual(set(message), MESSAGE_KEYS)

    def test_limit_is_capped_at_50_and_bad_values_fall_back(self):
        self.assertEqual(len(self.get(limit=1000).json()["results"]), 50)
        self.assertEqual(len(self.get(limit=5).json()["results"]), 5)
        for bad in ("0", "-3", "abc", ""):
            self.assertEqual(len(self.get(limit=bad).json()["results"]), 30, bad)

    def test_before_loads_older_messages(self):
        first_page = self.get().json()["results"]

        older = self.get(before=first_page[0]["id"]).json()

        self.assertEqual([m["id"] for m in older["results"]], self.ids[:30])
        self.assertFalse(older["has_more_older"])

    def test_before_with_small_limit(self):
        data = self.get(before=self.ids[10], limit=4).json()

        self.assertEqual([m["id"] for m in data["results"]], self.ids[6:10])
        self.assertTrue(data["has_more_older"])

    def test_after_returns_only_newer_messages_ascending(self):
        data = self.get(after=self.ids[-3]).json()

        self.assertEqual([m["id"] for m in data["results"]], self.ids[-2:])
        self.assertTrue(data["has_more_older"])  # старше первого присланного есть

    def test_after_the_last_returns_nothing(self):
        data = self.get(after=self.ids[-1]).json()

        self.assertEqual(data["results"], [])

    def test_after_respects_the_limit(self):
        data = self.get(after=self.ids[0], limit=5).json()

        self.assertEqual([m["id"] for m in data["results"]], self.ids[1:6])

    def test_bad_cursors_are_400(self):
        for params in ({"before": "abc"}, {"after": "0"}, {"before": "-1"}):
            self.assertEqual(self.get(**params).status_code, 400, params)

    def test_empty_conversation(self):
        empty = make_conversation(self.third, self.me, Status.ACCEPTED, first_body=None)

        data = self.client.get(url(empty, "messages/")).json()

        self.assertEqual(data, {"results": [], "has_more_older": False})

    def test_pending_request_messages_are_readable_by_both(self):
        pending = make_conversation(self.third, self.me, Status.PENDING, first_body="please talk")

        mine = self.client.get(url(pending, "messages/")).json()["results"]
        self.client.force_login(self.third)
        theirs = self.client.get(url(pending, "messages/")).json()["results"]

        self.assertEqual([m["body"] for m in mine], ["please talk"])
        self.assertFalse(mine[0]["sender_is_me"])
        self.assertTrue(theirs[0]["sender_is_me"])


class ReadTests(DecisionTestCase):
    def test_read_marks_only_incoming_messages(self):
        conversation = make_conversation(self.other, self.me, Status.ACCEPTED, first_body=None)
        incoming = [add_message(conversation, self.other, f"in{i}") for i in range(3)]
        mine = add_message(conversation, self.me, "out")
        self.client.force_login(self.me)

        response = self.client.post(url(conversation, "read/"))

        self.assertEqual(response.json(), {"updated": 3})
        for message in incoming:
            message.refresh_from_db()
            self.assertIsNotNone(message.seen_at)
        mine.refresh_from_db()
        self.assertIsNone(mine.seen_at)  # свои сообщения не помечаются
        self.assertEqual(self.client.post(url(conversation, "read/")).json(), {"updated": 0})  # повтор

    def test_read_marks_the_other_side_messages_only_for_the_reader(self):
        conversation = make_conversation(self.other, self.me, Status.ACCEPTED, first_body=None)
        add_message(conversation, self.me, "mine")
        add_message(conversation, self.other, "theirs")
        self.client.force_login(self.other)

        self.assertEqual(self.client.post(url(conversation, "read/")).json(), {"updated": 1})
        self.assertEqual(Message.objects.get(body="mine").seen_at is not None, True)
        self.assertIsNone(Message.objects.get(body="theirs").seen_at)

    def test_read_does_nothing_in_pending_or_declined(self):
        pending = make_conversation(self.other, self.me, Status.PENDING)
        declined = make_conversation(self.third, self.me, Status.DECLINED)
        self.client.force_login(self.me)

        self.assertEqual(self.client.post(url(pending, "read/")).json(), {"updated": 0})
        self.assertEqual(self.client.post(url(declined, "read/")).json(), {"updated": 0})
        self.assertFalse(Message.objects.exclude(seen_at=None).exists())  # инициатор не узнает, что открыли

    def test_only_post(self):
        conversation = make_conversation(self.other, self.me, Status.ACCEPTED)
        self.client.force_login(self.me)

        self.assertEqual(self.client.get(url(conversation, "read/")).status_code, 405)


@override_settings(THROTTLING_ENABLED=True)
class ThrottleTests(DecisionTestCase):
    def setUp(self):
        super().setUp()
        from django.core.cache import cache

        cache.clear()
        self.client.force_login(self.me)

    def test_11th_new_request_in_a_day_is_throttled(self):
        for i in range(10):
            person(f"target{i}")
            self.assertEqual(self.client.post(CONVERSATIONS, {"username": f"target{i}", "body": "hi"}, format="json").status_code, 201)
        person("target10")

        response = self.client.post(CONVERSATIONS, {"username": "target10", "body": "hi"}, format="json")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(error_of(response)["code"], "throttled")

    def test_31st_message_in_a_minute_is_throttled(self):
        conversation = make_conversation(self.other, self.me, Status.ACCEPTED)
        for _ in range(30):
            self.assertEqual(self.client.post(url(conversation, "messages/"), {"body": "x"}, format="json").status_code, 201)

        response = self.client.post(url(conversation, "messages/"), {"body": "x"}, format="json")

        self.assertEqual(response.status_code, 429)

    def test_daily_message_limit_is_a_separate_scope(self):
        from unittest import mock

        from rest_framework.throttling import UserRateThrottle

        conversation = make_conversation(self.other, self.me, Status.ACCEPTED)
        with mock.patch.dict(UserRateThrottle.THROTTLE_RATES, {"message_send_day": "3/day"}):
            codes = [
                self.client.post(url(conversation, "messages/"), {"body": "x"}, format="json").status_code
                for _ in range(4)
            ]

        self.assertEqual(codes, [201, 201, 201, 429])

    def test_reading_is_not_limited_by_the_message_scopes(self):
        for _ in range(35):
            self.assertEqual(self.client.get(CONVERSATIONS).status_code, 200)
