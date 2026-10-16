"""Эффекты блокировки: поиск, избранное, профиль, запросы на переписку и диалоги — в обе стороны."""

import json

from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from apps.messaging.models import Conversation
from apps.messaging.tests.helpers import (
    CONVERSATIONS,
    add_message,
    make_conversation,
    send_request,
    url as conversation_url,
)
from apps.moderation.models import Block
from apps.profiles.models import SavedProfile
from apps.users.tests.helpers import error_of

from .helpers import SAVED, SEARCH, block, person, usernames

Status = Conversation.Status
SUMMARY = f"{CONVERSATIONS}summary/"


def directions(a, b):
    """Обе стороны блокировки: (кто блокирует, кого блокируют, кто смотрит)."""
    return [("A blocks B", a, b), ("B blocks A", b, a)]


class SearchAndProfileTests(APITestCase):
    def setUp(self):
        self.a = person("alice")
        self.b = person("bob")
        self.c = person("carol")

    def test_blocked_people_are_hidden_from_search_in_both_directions(self):
        for label, blocker, blocked in directions(self.a, self.b):
            with self.subTest(label):
                Block.objects.all().delete()
                block(blocker, blocked)

                self.client.force_login(self.a)
                self.assertEqual(sorted(usernames(self.client.get(SEARCH))), ["carol"])
                self.client.force_login(self.b)
                self.assertEqual(sorted(usernames(self.client.get(SEARCH))), ["carol"])

    def test_text_search_does_not_find_a_blocked_person_either(self):
        block(self.a, self.b)

        self.client.force_login(self.a)
        self.assertEqual(usernames(self.client.get(SEARCH, {"q": "bob"})), [])
        self.client.force_login(self.b)
        self.assertEqual(usernames(self.client.get(SEARCH, {"q": "alice"})), [])

    def test_profile_is_404_in_both_directions_and_same_as_missing(self):
        for label, blocker, blocked in directions(self.a, self.b):
            with self.subTest(label):
                Block.objects.all().delete()
                block(blocker, blocked)

                self.client.force_login(self.a)
                to_b = self.client.get(f"{SEARCH}bob/")
                self.client.force_login(self.b)
                to_a = self.client.get(f"{SEARCH}alice/")
                missing = self.client.get(f"{SEARCH}nobody/")

                self.assertEqual((to_b.status_code, to_a.status_code), (404, 404))
                self.assertEqual(to_b.json(), missing.json())  # неотличимо от «нет такого»
                self.assertEqual(to_a.json(), missing.json())

    def test_unrelated_people_are_unaffected(self):
        block(self.a, self.b)
        self.client.force_login(self.c)

        self.assertEqual(sorted(usernames(self.client.get(SEARCH))), ["alice", "bob"])
        self.assertEqual(self.client.get(f"{SEARCH}alice/").status_code, 200)

    def test_unblocking_restores_everything(self):
        block(self.a, self.b)
        self.client.force_login(self.a)
        self.client.delete("/api/blocks/bob/")

        self.assertEqual(sorted(usernames(self.client.get(SEARCH))), ["bob", "carol"])
        self.assertEqual(self.client.get(f"{SEARCH}bob/").status_code, 200)


class SavedTests(APITestCase):
    def setUp(self):
        self.a = person("alice")
        self.b = person("bob")

    def test_saved_list_hides_blocked_people_in_both_directions(self):
        for label, blocker, blocked in directions(self.a, self.b):
            with self.subTest(label):
                Block.objects.all().delete()
                SavedProfile.objects.all().delete()
                SavedProfile.objects.create(owner=self.a, saved_user=self.b)
                SavedProfile.objects.create(owner=self.b, saved_user=self.a)
                block(blocker, blocked)

                self.client.force_login(self.a)
                self.assertEqual(usernames(self.client.get(SAVED)), [])
                self.client.force_login(self.b)
                self.assertEqual(usernames(self.client.get(SAVED)), [])

    def test_saved_bookmark_returns_after_unblock(self):
        SavedProfile.objects.create(owner=self.a, saved_user=self.b)
        block(self.a, self.b)
        self.client.force_login(self.a)
        self.assertEqual(usernames(self.client.get(SAVED)), [])

        self.client.delete("/api/blocks/bob/")

        self.assertEqual(usernames(self.client.get(SAVED)), ["bob"])

    def test_saving_a_blocked_person_is_404(self):
        for label, blocker, blocked in directions(self.a, self.b):
            with self.subTest(label):
                Block.objects.all().delete()
                block(blocker, blocked)
                self.client.force_login(self.a)

                self.assertEqual(self.client.put(f"{SAVED}bob/").status_code, 404)


class NewRequestTests(APITestCase):
    def setUp(self):
        self.a = person("alice")
        self.b = person("bob")

    def test_request_to_or_from_a_blocked_person_is_404(self):
        for label, blocker, blocked in directions(self.a, self.b):
            with self.subTest(label):
                Block.objects.all().delete()
                block(blocker, blocked)

                self.client.force_login(self.a)
                to_b = send_request(self.client, "bob")
                self.client.force_login(self.b)
                to_a = send_request(self.client, "alice")
                missing = send_request(self.client, "nobody")

                self.assertEqual((to_b.status_code, to_a.status_code), (404, 404))
                self.assertEqual(to_b.json(), missing.json())
                self.assertFalse(Conversation.objects.exists())

    def test_existing_conversation_does_not_reveal_the_block_on_new_request(self):
        make_conversation(self.a, self.b, Status.ACCEPTED)
        block(self.b, self.a)
        self.client.force_login(self.a)

        response = send_request(self.client, "bob")

        self.assertEqual(response.status_code, 404)  # а не 409 conversation_exists


class ConversationTests(APITestCase):
    def setUp(self):
        self.a = person("alice")
        self.b = person("bob")
        self.conversation = make_conversation(self.a, self.b, Status.ACCEPTED, first_body="hi")
        add_message(self.conversation, self.b, "unread from bob")

    def chats(self, user):
        self.client.force_login(user)
        return self.client.get(CONVERSATIONS, {"box": "chats"}).json()["results"]

    def summary(self, user):
        self.client.force_login(user)
        return self.client.get(SUMMARY).json()

    def test_blocker_loses_the_conversation_everywhere(self):
        block(self.a, self.b)

        self.assertEqual(self.chats(self.a), [])
        for box in ("requests", "sent"):
            self.assertEqual(self.client.get(CONVERSATIONS, {"box": box}).json()["results"], [])
        self.assertEqual(self.summary(self.a), {"unread_messages": 0, "pending_requests": 0})
        self.assertEqual(self.client.get(conversation_url(self.conversation)).status_code, 404)
        self.assertEqual(self.client.get(conversation_url(self.conversation, "messages/")).status_code, 404)

    def test_blocked_person_still_sees_the_conversation_unchanged(self):
        before = self.chats(self.b)
        block(self.a, self.b)

        after = self.chats(self.b)

        self.assertEqual(len(after), 1)
        self.assertEqual(after[0]["status"], "accepted")
        self.assertEqual(after[0]["id"], before[0]["id"])
        self.assertEqual(self.client.get(conversation_url(self.conversation)).status_code, 200)
        history = self.client.get(conversation_url(self.conversation, "messages/")).json()["results"]
        self.assertEqual([m["body"] for m in history], ["hi", "unread from bob"])

    def test_blocked_person_cannot_write_and_gets_a_neutral_error(self):
        block(self.a, self.b)
        self.client.force_login(self.b)

        response = self.client.post(
            conversation_url(self.conversation, "messages/"), {"body": "hello?"}, format="json"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(error_of(response)["code"], "conversation_closed")
        self.assertEqual(self.conversation.messages.count(), 2)

    def test_nothing_in_responses_reveals_the_block_to_the_blocked_person(self):
        block(self.a, self.b)
        self.client.force_login(self.b)

        texts = [
            self.client.get(CONVERSATIONS).content.decode(),
            self.client.get(SUMMARY).content.decode(),
            self.client.get(conversation_url(self.conversation)).content.decode(),
            self.client.get(conversation_url(self.conversation, "messages/")).content.decode(),
            self.client.post(
                conversation_url(self.conversation, "messages/"), {"body": "x"}, format="json"
            ).content.decode(),
            self.client.get("/api/blocks/").content.decode(),
        ]

        for text in texts:
            self.assertNotIn("block", text.lower())
        self.assertEqual(json.loads(texts[-1])["results"], [])

    def test_blocker_cannot_write_either(self):
        block(self.a, self.b)
        self.client.force_login(self.a)

        response = self.client.post(
            conversation_url(self.conversation, "messages/"), {"body": "hi"}, format="json"
        )

        self.assertEqual(response.status_code, 404)

    def test_both_sides_blocking_each_other_hides_it_for_both(self):
        block(self.a, self.b)
        block(self.b, self.a)

        self.assertEqual(self.chats(self.a), [])
        self.assertEqual(self.chats(self.b), [])

    def test_conversation_returns_in_the_same_status_after_unblocking(self):
        block(self.a, self.b)
        self.client.force_login(self.a)
        self.assertEqual(self.chats(self.a), [])

        self.client.delete("/api/blocks/bob/")

        chats = self.chats(self.a)
        self.assertEqual([c["status"] for c in chats], ["accepted"])
        self.assertEqual(chats[0]["unread_count"], 1)
        self.client.force_login(self.b)
        sent = self.client.post(
            conversation_url(self.conversation, "messages/"), {"body": "back again"}, format="json"
        )
        self.assertEqual(sent.status_code, 201)

    def test_unblocking_keeps_pending_conversation_pending(self):
        carol = person("carol")
        pending = make_conversation(self.a, carol, Status.PENDING)
        block(self.a, carol)
        self.client.force_login(self.a)

        self.client.delete("/api/blocks/carol/")

        pending.refresh_from_db()
        self.assertEqual(pending.status, Status.PENDING)
        self.assertEqual(len(self.client.get(CONVERSATIONS, {"box": "sent"}).json()["results"]), 1)

    def test_pending_requests_from_or_to_a_blocked_person_are_not_counted(self):
        carol = person("carol")
        make_conversation(carol, self.a, Status.PENDING)  # входящий запрос от carol
        self.assertEqual(self.summary(self.a)["pending_requests"], 1)

        block(carol, self.a)  # carol блокирует alice: запрос в счётчик не попадает
        self.assertEqual(self.summary(self.a)["pending_requests"], 0)
        requests = self.client.get(CONVERSATIONS, {"box": "requests"}).json()["results"]
        self.assertEqual(len(requests), 1)  # в списке запрос остаётся без изменений

        Block.objects.all().delete()
        block(self.a, carol)  # alice блокирует carol: диалог скрыт, счётчик 0
        self.assertEqual(self.summary(self.a)["pending_requests"], 0)

    def test_blocked_recipient_cannot_accept_or_decline(self):
        dave = person("dave")
        pending = make_conversation(self.a, dave, Status.PENDING)
        block(self.a, dave)
        self.client.force_login(dave)

        for action in ("accept/", "decline/"):
            with self.subTest(action):
                response = self.client.post(conversation_url(pending, action))
                self.assertEqual(response.status_code, 403)
                self.assertEqual(error_of(response)["code"], "conversation_closed")
        pending.refresh_from_db()
        self.assertEqual(pending.status, Status.PENDING)


class QueryCountTests(APITestCase):
    """Число SQL-запросов не растёт с числом блокировок (2 и 12)."""

    def count_queries(self, address, params=None):
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(address, params)
        self.assertEqual(response.status_code, 200)
        return len(context)

    def make_blocks(self, owner, how_many, start):
        for number in range(start, start + how_many):
            block(owner, person(f"blocked{number:02d}"))

    def test_search_query_count_does_not_grow_with_blocks(self):
        me = person("me_user")
        for number in range(5):
            person(f"visible{number}")
        self.client.force_login(me)
        self.make_blocks(me, 2, 0)
        few = self.count_queries(SEARCH)

        self.make_blocks(me, 10, 2)
        many = self.count_queries(SEARCH)

        self.assertEqual(few, many)

    def test_saved_query_count_does_not_grow_with_blocks(self):
        me = person("me_user")
        for number in range(3):
            SavedProfile.objects.create(owner=me, saved_user=person(f"saved{number}"))
        self.client.force_login(me)
        self.make_blocks(me, 2, 0)
        few = self.count_queries(SAVED)

        self.make_blocks(me, 10, 2)
        many = self.count_queries(SAVED)

        self.assertEqual(few, many)

    def test_conversation_list_and_summary_query_count_does_not_grow_with_blocks(self):
        me = person("me_user")
        for number in range(3):
            make_conversation(person(f"friend{number}"), me, Status.ACCEPTED)
        self.client.force_login(me)
        self.make_blocks(me, 2, 0)
        few = (self.count_queries(CONVERSATIONS), self.count_queries(SUMMARY))

        self.make_blocks(me, 10, 2)
        for number in range(4):  # заблокированные с диалогами тоже не добавляют запросов
            other = person(f"gone{number}")
            make_conversation(other, me, Status.ACCEPTED)
            block(me, other)
        many = (self.count_queries(CONVERSATIONS), self.count_queries(SUMMARY))

        self.assertEqual(few, many)
