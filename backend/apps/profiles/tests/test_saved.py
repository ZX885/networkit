import threading
from datetime import timedelta

from django.core.cache import cache
from django.db import IntegrityError, connection, connections, transaction
from django.test import TransactionTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.profiles.models import Profile, SavedProfile
from apps.profiles.tests.factories import birth_date_for_age
from apps.users.models import User
from apps.users.tests.helpers import error_of, make_account

LIST = "/api/saved/"
SEARCH = "/api/profiles/"

CARD_KEYS = {
    "username",
    "first_name",
    "last_name",
    "avatar_url",
    "field",
    "field_label",
    "status",
    "status_label",
    "city",
    "country",
    "country_label",
    "bio",
    "interests",
    "is_saved",
}

_numbers = iter(range(1, 100_000))


def person(**profile):
    """Подтверждённый человек с уникальной почтой и username (если не заданы)."""
    n = next(_numbers)
    profile.setdefault("username", f"person_{n}")
    return make_account(email=f"p{n}@example.com", **profile)


def url(username):
    return f"/api/saved/{username}/"


def save(owner, *targets):
    for target in targets:
        SavedProfile.objects.create(owner=owner, saved_user=target)


class SavedTestCase(APITestCase):
    def setUp(self):
        self.viewer = make_account(email="viewer@example.com", username="viewer")
        self.client.force_login(self.viewer)

    def saved_usernames(self, **params):
        response = self.client.get(LIST, params)
        self.assertEqual(response.status_code, 200, response.content)
        return [item["username"] for item in response.json()["results"]]


class SavedAddRemoveTests(SavedTestCase):
    def test_put_adds_and_is_idempotent(self):
        person(username="maria")

        first = self.client.put(url("maria"))
        second = self.client.put(url("maria"))

        self.assertEqual((first.status_code, second.status_code), (204, 204))
        self.assertEqual(first.content, b"")
        self.assertEqual(SavedProfile.objects.filter(owner=self.viewer).count(), 1)

    def test_delete_removes_and_is_idempotent(self):
        maria = person(username="maria")
        save(self.viewer, maria)

        first = self.client.delete(url("maria"))
        second = self.client.delete(url("maria"))

        self.assertEqual((first.status_code, second.status_code), (204, 204))
        self.assertFalse(SavedProfile.objects.filter(owner=self.viewer).exists())

    def test_delete_without_a_bookmark_or_for_unknown_username_is_204(self):
        person(username="maria")

        self.assertEqual(self.client.delete(url("maria")).status_code, 204)
        self.assertEqual(self.client.delete(url("nobody_here")).status_code, 204)

    def test_delete_works_for_a_banned_person_too(self):
        banned = person(username="banned_one")
        save(self.viewer, banned)
        User.objects.filter(pk=banned.pk).update(is_banned=True)

        self.assertEqual(self.client.delete(url("banned_one")).status_code, 204)
        self.assertFalse(SavedProfile.objects.filter(owner=self.viewer).exists())

    def test_username_is_case_insensitive(self):
        person(username="maria")

        self.assertEqual(self.client.put(url("MARIA")).status_code, 204)
        self.assertEqual(self.saved_usernames(), ["maria"])
        self.assertEqual(self.client.delete(url("Maria")).status_code, 204)
        self.assertEqual(self.saved_usernames(), [])

    def test_cannot_save_yourself(self):
        response = self.client.put(url("viewer"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_of(response)["code"], "cannot_target_self")
        self.assertFalse(SavedProfile.objects.exists())

    def test_unknown_banned_inactive_and_unverified_are_404(self):
        banned = person(username="banned_one")
        User.objects.filter(pk=banned.pk).update(is_banned=True)
        inactive = person(username="inactive_one")
        User.objects.filter(pk=inactive.pk).update(is_active=False)
        make_account(email="unv@example.com", verified=False, username="unverified")

        for name in ("nobody_here", "banned_one", "inactive_one", "unverified"):
            with self.subTest(name):
                response = self.client.put(url(name))
                self.assertEqual(response.status_code, 404)
                self.assertEqual(error_of(response)["code"], "not_found")
        self.assertFalse(SavedProfile.objects.exists())

    def test_account_without_profile_cannot_be_saved(self):
        from apps.profiles.tests.factories import make_user

        make_user(email="staff@example.com")

        self.assertEqual(self.client.put(url("staff")).status_code, 404)

    def test_requires_login_and_only_allowed_methods(self):
        person(username="maria")
        self.client.logout()

        for response in (
            self.client.get(LIST),
            self.client.put(url("maria")),
            self.client.delete(url("maria")),
        ):
            self.assertEqual(response.status_code, 401)
            self.assertEqual(error_of(response)["code"], "not_authenticated")

        self.client.force_login(self.viewer)
        self.assertEqual(self.client.post(url("maria"), {}, format="json").status_code, 405)
        self.assertEqual(self.client.get(url("maria")).status_code, 405)
        self.assertEqual(self.client.post(LIST, {}, format="json").status_code, 405)


class SavedListTests(SavedTestCase):
    def test_list_has_pagination_and_exact_card_keys_with_is_saved_true(self):
        save(self.viewer, person(username="maria"))

        data = self.client.get(LIST).json()

        self.assertEqual(set(data), {"count", "next", "previous", "results"})
        self.assertEqual(data["count"], 1)
        self.assertEqual(set(data["results"][0]), CARD_KEYS)
        self.assertTrue(data["results"][0]["is_saved"])

    def test_newest_bookmark_first(self):
        now = timezone.now()
        first, second, third = person(username="a_first"), person(username="b_second"), person(username="c_third")
        save(self.viewer, first, second, third)
        for target, days in ((first, 3), (second, 1), (third, 2)):
            SavedProfile.objects.filter(owner=self.viewer, saved_user=target).update(
                created_at=now - timedelta(days=days)
            )

        self.assertEqual(self.saved_usernames(), ["b_second", "c_third", "a_first"])

    def test_pagination(self):
        for _ in range(14):
            save(self.viewer, person())

        first = self.client.get(LIST).json()
        second = self.client.get(LIST, {"page": 2}).json()

        self.assertEqual((first["count"], len(first["results"])), (14, 12))
        self.assertEqual(len(second["results"]), 2)
        self.assertEqual(len(self.client.get(LIST, {"page_size": 1000}).json()["results"]), 14)
        self.assertEqual(self.client.get(LIST, {"page": 3}).status_code, 404)

    def test_other_peoples_bookmarks_are_not_visible(self):
        other = make_account(email="other@example.com", username="other")
        maria = person(username="maria")
        save(other, maria)

        self.assertEqual(self.saved_usernames(), [])
        self.assertEqual(self.client.get(f"{SEARCH}maria/").json()["is_saved"], False)

    def test_banned_inactive_and_unverified_disappear_from_the_list(self):
        keep = person(username="keep_me")
        banned = person(username="banned_one")
        inactive = person(username="inactive_one")
        unverified = make_account(email="unv@example.com", verified=False, username="unverified")
        save(self.viewer, keep, banned, inactive, unverified)
        User.objects.filter(pk=banned.pk).update(is_banned=True)
        User.objects.filter(pk=inactive.pk).update(is_active=False)

        self.assertEqual(self.saved_usernames(), ["keep_me"])
        self.assertEqual(self.client.get(LIST).json()["count"], 1)

        User.objects.filter(pk=banned.pk).update(is_banned=False)  # разбан — закладка вернулась
        self.assertEqual(set(self.saved_usernames()), {"keep_me", "banned_one"})

    def test_bookmark_stays_when_the_person_hides_from_search(self):
        hidden = person(username="hides_later")
        save(self.viewer, hidden)
        Profile.objects.filter(user=hidden).update(show_in_search=False)

        self.assertEqual(self.saved_usernames(), ["hides_later"])
        self.assertNotIn("hides_later", [i["username"] for i in self.client.get(SEARCH).json()["results"]])

    def test_privacy_rules_apply_to_saved_cards(self):
        hidden = person(
            username="hidden_one", show_location=False, university="Secret Uni", show_university=False
        )
        teen = person(
            username="teen_one", date_of_birth=birth_date_for_age(16), school="Secret High School"
        )
        save(self.viewer, hidden, teen)

        response = self.client.get(LIST)
        cards = {item["username"]: item for item in response.json()["results"]}
        raw = response.content.decode()

        self.assertIsNone(cards["hidden_one"]["city"])
        self.assertIsNone(cards["hidden_one"]["country"])
        self.assertIsNone(cards["hidden_one"]["country_label"])
        for card in cards.values():
            self.assertNotIn("school", card)
        for forbidden in ("email", "date_of_birth", "Secret Uni", "Secret High School", "gender"):
            self.assertNotIn(forbidden, raw)

    def test_adding_through_the_api_shows_up_in_the_list(self):
        person(username="maria")

        self.client.put(url("maria"))

        self.assertEqual(self.saved_usernames(), ["maria"])
        self.client.delete(url("maria"))
        self.assertEqual(self.saved_usernames(), [])


class IsSavedFlagTests(SavedTestCase):
    def test_search_cards_and_public_profile_show_the_real_flag(self):
        maria, john = person(username="maria"), person(username="john")
        self.client.put(url("maria"))

        cards = {i["username"]: i for i in self.client.get(SEARCH).json()["results"]}
        self.assertTrue(cards["maria"]["is_saved"])
        self.assertFalse(cards["john"]["is_saved"])
        self.assertTrue(self.client.get(f"{SEARCH}maria/").json()["is_saved"])
        self.assertFalse(self.client.get(f"{SEARCH}john/").json()["is_saved"])

        self.client.delete(url("maria"))
        self.assertFalse(self.client.get(f"{SEARCH}maria/").json()["is_saved"])
        self.assertFalse({i["username"]: i for i in self.client.get(SEARCH).json()["results"]}["maria"]["is_saved"])
        self.assertIsNotNone(john)

    def test_someone_elses_bookmark_does_not_set_is_saved_for_me(self):
        other = make_account(email="other@example.com", username="other")
        maria = person(username="maria")
        save(other, maria)

        cards = {i["username"]: i for i in self.client.get(SEARCH).json()["results"]}

        self.assertFalse(cards["maria"]["is_saved"])
        self.assertFalse(self.client.get(f"{SEARCH}maria/").json()["is_saved"])

    def test_own_public_profile_is_not_saved(self):
        self.assertFalse(self.client.get(f"{SEARCH}viewer/").json()["is_saved"])


class SavedQueryCountTests(SavedTestCase):
    """Число SQL-запросов не зависит от числа карточек (нет N+1)."""

    def count_queries(self, path, params=None):
        self.client.get(path, params)  # прогрев (сессия, кэши)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(path, params)
        self.assertEqual(response.status_code, 200)
        return len(queries)

    def test_search_list_saved_list_and_profile_do_not_grow_with_cards(self):
        people = [person() for _ in range(2)]
        save(self.viewer, *people)
        small = {
            "search": self.count_queries(SEARCH),
            "saved": self.count_queries(LIST),
        }

        more = [person() for _ in range(10)]
        save(self.viewer, *more[:6])
        large = {
            "search": self.count_queries(SEARCH),
            "saved": self.count_queries(LIST),
        }

        self.assertEqual(large, small)
        self.assertGreater(len(self.client.get(SEARCH).json()["results"]), 10)

    def test_is_saved_costs_one_query_per_page_in_search(self):
        for _ in range(3):
            person()
        with_saved_off = self.count_queries(SEARCH)
        # без закладок в списке достаточно того же запроса: сравниваем с ситуацией «закладки есть»
        for target in User.objects.exclude(pk=self.viewer.pk):
            save(self.viewer, target)

        self.assertEqual(self.count_queries(SEARCH), with_saved_off)

    def test_public_profile_does_not_grow(self):
        maria = person(username="maria")
        before = self.count_queries(f"{SEARCH}maria/")
        save(self.viewer, maria)

        self.assertEqual(self.count_queries(f"{SEARCH}maria/"), before)


class SavedDatabaseTests(SavedTestCase):
    def test_deleting_the_owner_removes_their_bookmarks(self):
        maria = person(username="maria")
        save(self.viewer, maria)

        self.viewer.delete()

        self.assertEqual(SavedProfile.objects.count(), 0)
        self.assertTrue(User.objects.filter(pk=maria.pk).exists())

    def test_deleting_the_saved_person_removes_bookmarks_on_them(self):
        maria = person(username="maria")
        save(self.viewer, maria)

        maria.delete()

        self.assertEqual(SavedProfile.objects.count(), 0)
        self.assertEqual(self.saved_usernames(), [])

    def test_database_refuses_duplicates_and_self_bookmarks(self):
        maria = person(username="maria")
        save(self.viewer, maria)

        with self.assertRaises(IntegrityError), transaction.atomic():
            SavedProfile.objects.create(owner=self.viewer, saved_user=maria)
        with self.assertRaises(IntegrityError), transaction.atomic():
            SavedProfile.objects.create(owner=self.viewer, saved_user=self.viewer)


@override_settings(THROTTLING_ENABLED=True)
class SavedThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.viewer = make_account(email="viewer@example.com", username="viewer")
        self.client.force_login(self.viewer)
        person(username="maria")

    def test_61st_change_in_a_minute_is_throttled(self):
        for _ in range(60):
            self.assertEqual(self.client.put(url("maria")).status_code, 204)

        response = self.client.delete(url("maria"))

        self.assertEqual(response.status_code, 429)
        self.assertEqual(error_of(response)["code"], "throttled")

    def test_limit_is_per_user(self):
        for _ in range(60):
            self.client.put(url("maria"))
        other = make_account(email="other@example.com", username="other")
        self.client.force_login(other)

        self.assertEqual(self.client.put(url("maria")).status_code, 204)


@override_settings(SAVED_MAX=3)
class SavedLimitTests(SavedTestCase):
    """Лимит закладок (в этих тестах 3; настоящее значение 200 проверяет SavedRealLimitTests)."""

    def test_the_last_allowed_one_passes_and_the_next_gets_409(self):
        targets = [person(username=f"target{i}") for i in range(4)]

        for target in targets[:3]:
            self.assertEqual(self.client.put(url(target.profile.username)).status_code, 204)
        response = self.client.put(url("target3"))

        self.assertEqual(response.status_code, 409)
        self.assertEqual(error_of(response)["code"], "saved_limit_reached")
        self.assertEqual(SavedProfile.objects.filter(owner=self.viewer).count(), 3)
        self.assertFalse(SavedProfile.objects.filter(saved_user=targets[3]).exists())

    def test_repeating_an_already_saved_one_at_full_limit_is_204(self):
        targets = [person(username=f"target{i}") for i in range(3)]
        save(self.viewer, *targets)

        self.assertEqual(self.client.put(url("target0")).status_code, 204)
        self.assertEqual(self.client.put(url("target2")).status_code, 204)
        self.assertEqual(SavedProfile.objects.filter(owner=self.viewer).count(), 3)

    def test_after_deleting_one_a_new_one_can_be_added(self):
        targets = [person(username=f"target{i}") for i in range(4)]
        save(self.viewer, *targets[:3])
        self.assertEqual(self.client.put(url("target3")).status_code, 409)

        self.assertEqual(self.client.delete(url("target0")).status_code, 204)

        self.assertEqual(self.client.put(url("target3")).status_code, 204)
        self.assertEqual(self.client.put(url("target0")).status_code, 409)

    def test_the_limit_is_per_owner(self):
        targets = [person(username=f"target{i}") for i in range(4)]
        other = make_account(email="other@example.com", username="other")
        save(other, *targets[:3])

        self.assertEqual(self.client.put(url("target3")).status_code, 204)

    def test_hidden_bookmarks_do_not_use_up_the_limit(self):
        banned = person(username="banned_one")
        save(self.viewer, banned)
        User.objects.filter(pk=banned.pk).update(is_banned=True)
        targets = [person(username=f"target{i}") for i in range(3)]

        for target in targets:
            self.assertEqual(self.client.put(url(target.profile.username)).status_code, 204)

    def test_limit_is_exposed_in_meta(self):
        self.client.logout()

        limits = self.client.get("/api/meta/").json()["limits"]

        self.assertIn("saved_max", limits)


class SavedRealLimitTests(SavedTestCase):
    def test_the_200th_passes_and_the_201st_gets_409(self):
        now = timezone.now()
        users = User.objects.bulk_create(
            [User(email=f"bulk{i}@example.com", email_verified_at=now) for i in range(199)]
        )
        Profile.objects.bulk_create(
            [
                Profile(
                    user=user,
                    username=f"bulk_{i}",
                    first_name="Bulk",
                    last_name="Person",
                    date_of_birth=birth_date_for_age(25),
                    country="UZ",
                    city="Tashkent",
                    status="student",
                    field="computer_science",
                )
                for i, user in enumerate(users)
            ]
        )
        SavedProfile.objects.bulk_create(
            [SavedProfile(owner=self.viewer, saved_user=user) for user in users]
        )
        person(username="number200")
        person(username="number201")

        self.assertEqual(self.client.put(url("number200")).status_code, 204)  # 200-я проходит
        response = self.client.put(url("number201"))  # 201-я — нет

        self.assertEqual(response.status_code, 409)
        self.assertEqual(error_of(response)["code"], "saved_limit_reached")
        self.assertEqual(self.client.put(url("number200")).status_code, 204)  # повтор при полном лимите
        self.assertEqual(SavedProfile.objects.filter(owner=self.viewer).count(), 200)

    def test_meta_reports_the_limit(self):
        self.assertEqual(self.client.get("/api/meta/").json()["limits"]["saved_max"], 200)


@override_settings(SAVED_MAX=3)
class SavedConcurrencyTests(TransactionTestCase):
    """Параллельные запросы одного человека не могут вместе обойти лимит."""

    def test_parallel_puts_cannot_exceed_the_limit(self):
        owner = make_account(email="owner@example.com", username="owner")
        existing = [make_account(email=f"e{i}@example.com", username=f"existing{i}") for i in range(2)]
        save(owner, *existing)
        targets = [make_account(email=f"t{i}@example.com", username=f"parallel{i}") for i in range(6)]
        results = []
        barrier = threading.Barrier(len(targets))

        def worker(username):
            try:
                client = APIClient()
                client.force_authenticate(owner)
                barrier.wait(timeout=10)
                results.append(client.put(url(username)).status_code)
            finally:
                connections.close_all()

        threads = [threading.Thread(target=worker, args=(t.profile.username,)) for t in targets]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=60)

        self.assertEqual(sorted(results), [204, 409, 409, 409, 409, 409])
        self.assertEqual(SavedProfile.objects.filter(owner=owner).count(), 3)
