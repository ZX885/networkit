import threading
from datetime import timedelta

from django.db import connections
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.messaging.models import Conversation, Message
from apps.profiles.models import Profile
from apps.users.models import User
from apps.users.tests.helpers import error_of, field_codes

from .helpers import CONVERSATION_KEYS, CONVERSATIONS, MESSAGE_KEYS, make_conversation, person, send_request

Status = Conversation.Status


class RequestTestCase(APITestCase):
    def setUp(self):
        self.me = person("me_user")
        self.client.force_login(self.me)


class CreateRequestTests(RequestTestCase):
    def test_creates_pending_conversation_with_first_message(self):
        other = person("maria")

        response = send_request(self.client, "maria", "  Hello Maria!  ")

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(set(data), {"conversation", "message"})
        self.assertEqual(set(data["conversation"]), CONVERSATION_KEYS)
        self.assertEqual(set(data["message"]), MESSAGE_KEYS)
        self.assertEqual(data["conversation"]["status"], "pending")
        self.assertTrue(data["conversation"]["initiated_by_me"])
        self.assertEqual(data["message"]["body"], "Hello Maria!")  # strip
        self.assertTrue(data["message"]["sender_is_me"])
        conversation = Conversation.objects.get()
        self.assertEqual(conversation.initiator, self.me)
        self.assertEqual({conversation.user_a, conversation.user_b}, {self.me, other})
        self.assertLess(conversation.user_a_id, conversation.user_b_id)
        self.assertIsNotNone(conversation.last_message_at)
        self.assertEqual(Message.objects.filter(conversation=conversation).count(), 1)

    def test_pair_is_stored_ordered_whoever_writes_first(self):
        older, newer = person("older_one"), person("newer_one")
        self.client.force_login(newer)

        send_request(self.client, "older_one")

        conversation = Conversation.objects.get()
        self.assertEqual((conversation.user_a, conversation.user_b), (older, newer))
        self.assertEqual(conversation.initiator, newer)

    def test_line_breaks_are_normalized_and_text_is_not_touched(self):
        person("maria")

        response = send_request(self.client, "maria", "line1\r\nline2\rline3 <b>bold</b> & \"q\"")

        self.assertEqual(response.json()["message"]["body"], 'line1\nline2\nline3 <b>bold</b> & "q"')

    def test_username_is_case_insensitive(self):
        person("maria")

        self.assertEqual(send_request(self.client, "MARIA").status_code, 201)

    def test_body_validation(self):
        person("maria")

        for body, code in (("", "required"), ("   \n ", "required"), ("x" * 501, "too_long")):
            with self.subTest(body[:5]):
                response = send_request(self.client, "maria", body)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(field_codes(response, "body"), [code])
        self.assertEqual(send_request(self.client, "maria", "x" * 500).status_code, 201)

    def test_missing_or_non_string_body_and_non_object_request(self):
        person("maria")

        self.assertEqual(self.client.post(CONVERSATIONS, {"username": "maria"}, format="json").status_code, 400)
        self.assertEqual(
            self.client.post(CONVERSATIONS, {"username": "maria", "body": 5}, format="json").status_code, 400
        )
        self.assertEqual(self.client.post(CONVERSATIONS, [1], format="json").status_code, 400)

    def test_cannot_message_yourself(self):
        response = send_request(self.client, "me_user")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_of(response)["code"], "cannot_target_self")
        self.assertFalse(Conversation.objects.exists())

    def test_unknown_banned_inactive_unverified_and_profileless_targets_are_404(self):
        banned = person("banned_one")
        User.objects.filter(pk=banned.pk).update(is_banned=True)
        inactive = person("inactive_one")
        User.objects.filter(pk=inactive.pk).update(is_active=False)
        from apps.users.tests.helpers import make_account

        make_account(email="unv@example.com", verified=False, username="unverified")
        from apps.profiles.tests.factories import make_user

        make_user(email="staff@example.com")

        for name in ("nobody_here", "banned_one", "inactive_one", "unverified", "staff"):
            with self.subTest(name):
                response = send_request(self.client, name)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(error_of(response)["code"], "not_found")
        self.assertFalse(Conversation.objects.exists())

    def test_person_hidden_from_search_can_still_be_messaged(self):
        person("hidden_one", show_in_search=False)

        self.assertEqual(send_request(self.client, "hidden_one").status_code, 201)

    def test_requires_login(self):
        self.client.logout()

        response = send_request(self.client, "maria")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(error_of(response)["code"], "not_authenticated")


class ConflictTests(RequestTestCase):
    def test_conversation_exists_when_already_accepted(self):
        other = person("maria")
        conversation = make_conversation(self.me, other, Status.ACCEPTED)

        response = send_request(self.client, "maria")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(error_of(response)["code"], "conversation_exists")
        self.assertEqual(error_of(response)["conversation_id"], str(conversation.pk))

    def test_conversation_exists_also_when_they_started_and_it_was_accepted(self):
        other = person("maria")
        conversation = make_conversation(other, self.me, Status.ACCEPTED)

        response = send_request(self.client, "maria")

        self.assertEqual(error_of(response)["code"], "conversation_exists")
        self.assertEqual(error_of(response)["conversation_id"], str(conversation.pk))

    def test_request_pending_when_i_already_sent_one(self):
        other = person("maria")
        conversation = make_conversation(self.me, other, Status.PENDING)

        response = send_request(self.client, "maria")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(error_of(response)["code"], "request_pending")
        self.assertEqual(error_of(response)["conversation_id"], str(conversation.pk))

    def test_request_pending_also_after_a_decline_masking(self):
        other = person("maria")
        make_conversation(self.me, other, Status.DECLINED)

        response = send_request(self.client, "maria")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(error_of(response)["code"], "request_pending")  # отказ не раскрывается

    def test_incoming_request_exists(self):
        other = person("maria")
        conversation = make_conversation(other, self.me, Status.PENDING)

        response = send_request(self.client, "maria")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(error_of(response)["code"], "incoming_request_exists")
        self.assertEqual(error_of(response)["conversation_id"], str(conversation.pk))

    def test_my_own_declined_incoming_request_is_closed(self):
        other = person("maria")
        make_conversation(other, self.me, Status.DECLINED)

        response = send_request(self.client, "maria")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(error_of(response)["code"], "conversation_closed")

    def test_second_request_creates_nothing(self):
        person("maria")
        send_request(self.client, "maria")

        send_request(self.client, "maria", "again")

        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 1)


@override_settings(PENDING_REQUESTS_MAX=2)
class PendingRequestsLimitTests(RequestTestCase):
    def targets(self, n):
        return [person(f"target{i}") for i in range(n)]

    def test_pending_requests_count_and_the_next_one_is_refused(self):
        a, b, c = self.targets(3)
        make_conversation(self.me, a, Status.PENDING)
        make_conversation(self.me, b, Status.PENDING)

        response = send_request(self.client, "target2")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(error_of(response)["code"], "pending_requests_limit_reached")
        self.assertFalse(Conversation.objects.filter(user_a=c).exists() or Conversation.objects.filter(user_b=c).exists())

    def test_declined_counts_for_less_than_seven_days(self):
        a, b, c = self.targets(3)
        make_conversation(self.me, a, Status.PENDING)
        declined = make_conversation(self.me, b, Status.DECLINED)
        Conversation.objects.filter(pk=declined.pk).update(
            decided_at=timezone.now() - timedelta(days=6, hours=23)
        )

        self.assertEqual(send_request(self.client, "target2").status_code, 409)  # 6 дней 23 часа — считается

    def test_declined_stops_counting_after_seven_days(self):
        a, b, c = self.targets(3)
        make_conversation(self.me, a, Status.PENDING)
        declined = make_conversation(self.me, b, Status.DECLINED)
        Conversation.objects.filter(pk=declined.pk).update(
            decided_at=timezone.now() - timedelta(days=7, minutes=1)
        )

        self.assertEqual(send_request(self.client, "target2").status_code, 201)  # 7 дней — уже нет

    def test_accepted_never_counts(self):
        a, b, c = self.targets(3)
        make_conversation(self.me, a, Status.ACCEPTED)
        make_conversation(self.me, b, Status.ACCEPTED)

        self.assertEqual(send_request(self.client, "target2").status_code, 201)

    def test_incoming_requests_do_not_count(self):
        a, b, c = self.targets(3)
        make_conversation(a, self.me, Status.PENDING)
        make_conversation(b, self.me, Status.PENDING)

        self.assertEqual(send_request(self.client, "target2").status_code, 201)

    def test_limit_is_per_person(self):
        a, b, c = self.targets(3)
        other = person("someone_else")
        make_conversation(other, a, Status.PENDING)
        make_conversation(other, b, Status.PENDING)

        self.assertEqual(send_request(self.client, "target2").status_code, 201)


class RaceTests(TransactionTestCase):
    """Два человека одновременно отправляют запросы друг другу: ровно один диалог и 409, не 500."""

    def test_opposite_requests_at_the_same_time(self):
        alice, bob = person("alice_x"), person("bob_x")
        barrier = threading.Barrier(2)
        results = []

        def worker(sender, target):
            try:
                client = APIClient()
                client.force_authenticate(sender)
                barrier.wait(timeout=10)
                response = send_request(client, target)
                results.append((response.status_code, response.json().get("error", {}).get("code")))
            finally:
                connections.close_all()

        threads = [
            threading.Thread(target=worker, args=(alice, "bob_x")),
            threading.Thread(target=worker, args=(bob, "alice_x")),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=60)

        statuses = sorted(code for code, _ in results)
        self.assertEqual(statuses, [201, 409])
        conflict = next(code for status, code in results if status == 409)
        self.assertIn(conflict, {"incoming_request_exists", "request_pending"})
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Profile.objects.count(), 2)

    def test_same_request_twice_at_the_same_time(self):
        alice = person("alice_y")
        person("bob_y")
        barrier = threading.Barrier(2)
        results = []

        def worker():
            try:
                client = APIClient()
                client.force_authenticate(alice)
                barrier.wait(timeout=10)
                results.append(send_request(client, "bob_y").status_code)
            finally:
                connections.close_all()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=60)

        self.assertEqual(sorted(results), [201, 409])
        self.assertEqual(Conversation.objects.count(), 1)
