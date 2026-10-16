from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.moderation.models import Block
from apps.profiles.tests.factories import make_user
from apps.users.models import User
from apps.users.tests.helpers import error_of

from .helpers import BLOCKS, MINI_CARD_KEYS, block, person


def url(username):
    return f"{BLOCKS}{username}/"


class BlockApiTests(APITestCase):
    def setUp(self):
        self.me = person("me_user")
        self.maria = person("maria", first_name="Maria", last_name="Karimova")
        self.client.force_login(self.me)

    def test_put_blocks_and_is_idempotent(self):
        first = self.client.put(url("maria"))
        second = self.client.put(url("maria"))

        self.assertEqual((first.status_code, second.status_code), (204, 204))
        self.assertEqual(Block.objects.filter(blocker=self.me, blocked=self.maria).count(), 1)

    def test_username_is_case_insensitive(self):
        self.assertEqual(self.client.put(url("MARIA")).status_code, 204)
        self.assertTrue(Block.objects.filter(blocker=self.me, blocked=self.maria).exists())

    def test_blocking_yourself_is_rejected(self):
        response = self.client.put(url("me_user"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_of(response)["code"], "cannot_target_self")
        self.assertFalse(Block.objects.exists())

    def test_unknown_unverified_or_banned_person_is_404(self):
        from apps.users.tests.helpers import make_account

        make_account(email="new@example.com", username="newbie", verified=False)
        banned = person("banned_one")
        User.objects.filter(pk=banned.pk).update(is_banned=True)

        for name in ("nobody", "newbie", "banned_one"):
            with self.subTest(name):
                self.assertEqual(self.client.put(url(name)).status_code, 404)
        self.assertFalse(Block.objects.exists())

    def test_blocking_someone_who_blocked_you_looks_the_same(self):
        block(self.maria, self.me)

        response = self.client.put(url("maria"))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Block.objects.count(), 2)

    def test_delete_unblocks_and_is_idempotent(self):
        block(self.me, self.maria)

        first = self.client.delete(url("maria"))
        second = self.client.delete(url("maria"))
        unknown = self.client.delete(url("nobody"))

        self.assertEqual((first.status_code, second.status_code, unknown.status_code), (204, 204, 204))
        self.assertFalse(Block.objects.exists())

    def test_delete_does_not_touch_the_block_made_by_the_other_person(self):
        block(self.maria, self.me)

        self.assertEqual(self.client.delete(url("maria")).status_code, 204)

        self.assertTrue(Block.objects.filter(blocker=self.maria, blocked=self.me).exists())

    def test_anonymous_cannot_use_the_api(self):
        self.client.logout()

        for method, address in (("get", BLOCKS), ("put", url("maria")), ("delete", url("maria"))):
            with self.subTest(method):
                self.assertIn(getattr(self.client, method)(address).status_code, (401, 403))

    @override_settings(BLOCKS_MAX=2)
    def test_limit_of_blocked_people(self):
        person("pone"), person("ptwo")
        self.assertEqual(self.client.put(url("maria")).status_code, 204)
        self.assertEqual(self.client.put(url("pone")).status_code, 204)

        response = self.client.put(url("ptwo"))

        self.assertEqual(response.status_code, 409)
        self.assertEqual(error_of(response)["code"], "blocks_limit_reached")
        self.assertEqual(self.client.put(url("maria")).status_code, 204)  # повтор уже заблокированного


class BlockListTests(APITestCase):
    def setUp(self):
        self.me = person("me_user")
        self.client.force_login(self.me)

    def test_list_has_exact_keys_and_pagination(self):
        maria = person("maria", first_name="Maria", last_name="Karimova")
        block(self.me, maria)

        data = self.client.get(BLOCKS).json()

        self.assertEqual(set(data), {"count", "next", "previous", "results"})
        self.assertEqual(data["count"], 1)
        self.assertEqual(set(data["results"][0]), MINI_CARD_KEYS)
        self.assertEqual(
            data["results"][0],
            {"username": "maria", "first_name": "Maria", "last_name": "Karimova", "avatar_url": None},
        )

    def test_newest_first_and_only_my_blocks(self):
        first, second, third = person("first"), person("second"), person("third")
        block(self.me, first)
        block(self.me, second)
        block(third, self.me)  # меня заблокировали: в моём списке этого нет

        usernames = [item["username"] for item in self.client.get(BLOCKS).json()["results"]]

        self.assertEqual(usernames, ["second", "first"])

    def test_response_has_no_private_fields(self):
        block(self.me, person("maria"))

        text = self.client.get(BLOCKS).content.decode()

        self.assertNotIn("email", text)
        self.assertNotIn("date_of_birth", text)

    def test_pagination_works(self):
        for number in range(13):
            block(self.me, person(f"user{number:02d}"))

        page1 = self.client.get(BLOCKS).json()
        page2 = self.client.get(BLOCKS, {"page": 2}).json()

        self.assertEqual((page1["count"], len(page1["results"]), len(page2["results"])), (13, 12, 1))


@override_settings(THROTTLING_ENABLED=True)
class BlockThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.me = person("me_user")
        self.client.force_login(self.me)
        person("maria")

    def test_31st_change_in_an_hour_is_throttled(self):
        for _ in range(30):
            self.assertEqual(self.client.put(url("maria")).status_code, 204)

        response = self.client.delete(url("maria"))

        self.assertEqual(response.status_code, 429)
        self.assertEqual(error_of(response)["code"], "throttled")

    def test_listing_is_not_limited_by_the_block_throttle(self):
        for _ in range(30):
            self.client.put(url("maria"))

        self.assertEqual(self.client.get(BLOCKS).status_code, 200)


class BlockDatabaseTests(APITestCase):
    def test_self_block_is_rejected_by_the_database(self):
        user = make_user()

        with self.assertRaises(IntegrityError), transaction.atomic():
            Block.objects.create(blocker=user, blocked=user)

    def test_duplicate_block_is_rejected_by_the_database(self):
        a, b = make_user(), make_user()
        Block.objects.create(blocker=a, blocked=b)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Block.objects.create(blocker=a, blocked=b)

        Block.objects.create(blocker=b, blocked=a)  # встречная блокировка — отдельная запись

    def test_blocks_are_deleted_with_either_user(self):
        a, b, c = make_user(), make_user(), make_user()
        Block.objects.create(blocker=a, blocked=b)
        Block.objects.create(blocker=c, blocked=a)

        a.delete()

        self.assertFalse(Block.objects.exists())
