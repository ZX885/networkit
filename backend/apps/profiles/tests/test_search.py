from datetime import timedelta

from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.profiles.models import Profile
from apps.profiles.tests.factories import birth_date_for_age
from apps.users.models import User
from apps.users.tests.helpers import error_of, field_codes, make_account

LIST = "/api/profiles/"

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

_numbers = iter(range(1, 10_000))


def person(**profile):
    """Подтверждённый человек с уникальной почтой и username (если не заданы)."""
    n = next(_numbers)
    profile.setdefault("username", f"person_{n}")
    return make_account(email=f"p{n}@example.com", **profile)


class SearchTestCase(APITestCase):
    def setUp(self):
        self.viewer = make_account(email="viewer@example.com", username="viewer")
        self.client.force_login(self.viewer)

    def search(self, **params):
        return self.client.get(LIST, params)

    def usernames(self, **params):
        response = self.search(**params)
        self.assertEqual(response.status_code, 200, response.content)
        return [item["username"] for item in response.json()["results"]]


class SearchVisibilityTests(SearchTestCase):
    def test_requires_login(self):
        self.client.logout()

        response = self.search()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(error_of(response)["code"], "not_authenticated")

    def test_own_profile_is_not_in_results(self):
        person(username="other")

        self.assertEqual(self.usernames(), ["other"])

    def test_banned_unverified_inactive_and_hidden_from_search_are_excluded(self):
        person(username="visible")
        banned = person(username="banned_one")
        User.objects.filter(pk=banned.pk).update(is_banned=True)
        make_account(email="unverified@example.com", verified=False, username="unverified")
        inactive = person(username="inactive_one")
        User.objects.filter(pk=inactive.pk).update(is_active=False)
        person(username="hidden_one", show_in_search=False)

        self.assertEqual(self.usernames(), ["visible"])

    def test_response_has_pagination_and_exact_card_keys(self):
        person(username="somebody")

        data = self.search().json()

        self.assertEqual(set(data), {"count", "next", "previous", "results"})
        self.assertEqual(data["count"], 1)
        self.assertEqual(set(data["results"][0]), CARD_KEYS)

    def test_no_private_data_in_the_json(self):
        person(username="secretive", gender="female", telegram="secretive_tg", show_contacts=True)

        raw = self.search().content.decode()

        for forbidden in (
            "email",
            "date_of_birth",
            "is_banned",
            "phone",
            "gender",
            "privacy",
            "secretive_tg",
            "example.com",
            '"age"',
            '"school"',
            '"university"',
        ):
            self.assertNotIn(forbidden, raw)

    def test_card_labels_and_defaults(self):
        person(username="labelled", country="UZ", field="computer_science", status="student")

        card = self.search().json()["results"][0]

        self.assertEqual(card["country_label"], "Uzbekistan")
        self.assertEqual(card["field_label"], "Computer Science")
        self.assertEqual(card["status_label"], "Student")
        self.assertIsNone(card["avatar_url"])
        self.assertFalse(card["is_saved"])

    def test_hidden_location_is_null_in_card(self):
        person(username="nowhere", show_location=False)

        card = self.search().json()["results"][0]

        self.assertIsNone(card["city"])
        self.assertIsNone(card["country"])
        self.assertIsNone(card["country_label"])


class SearchPrivacyRulesTests(SearchTestCase):
    """Поиск и фильтры не используют скрытые данные (docs/SPEC.md §6.3)."""

    def test_hidden_university_is_not_found_by_its_name(self):
        person(username="hidden_uni", university="Zorblax Institute", show_university=False)
        person(username="shown_uni", university="Zorblax Institute", show_university=True)

        self.assertEqual(self.usernames(q="Zorblax"), ["shown_uni"])

    def test_hidden_location_is_not_found_by_country_filter(self):
        person(username="uz_hidden", country="UZ", show_location=False)
        person(username="uz_shown", country="UZ", show_location=True)

        self.assertEqual(self.usernames(country="UZ"), ["uz_shown"])

    def test_hidden_location_is_not_found_by_city_or_region_text(self):
        person(username="city_hidden", city="Quuxville", region="Wobblia", show_location=False)
        person(username="city_shown", city="Quuxville", region="Wobblia", show_location=True)

        self.assertEqual(self.usernames(q="Quuxville"), ["city_shown"])
        self.assertEqual(self.usernames(q="Wobblia"), ["city_shown"])

    def test_public_filters_work_even_when_everything_else_is_hidden(self):
        person(
            username="private_one",
            show_location=False,
            show_university=False,
            field="law",
            status="professional",
            goals=["mentorship"],
            languages=["uzbek"],
        )

        self.assertEqual(self.usernames(field="law"), ["private_one"])
        self.assertEqual(self.usernames(status="professional"), ["private_one"])
        self.assertEqual(self.usernames(goal="mentorship"), ["private_one"])
        self.assertEqual(self.usernames(language="uzbek"), ["private_one"])


class SearchQueryTests(SearchTestCase):
    def test_q_matches_first_last_name_and_username_partially(self):
        person(username="aaa_one", first_name="Zuleyka", last_name="Brown")
        person(username="bbb_two", first_name="Mark", last_name="Quenby")
        person(username="ccc_xylo", first_name="Nina", last_name="Gray")

        self.assertEqual(self.usernames(q="zuley"), ["aaa_one"])
        self.assertEqual(self.usernames(q="QUENB"), ["bbb_two"])
        self.assertEqual(self.usernames(q="xylo"), ["ccc_xylo"])

    def test_every_word_must_match(self):
        person(username="dd_one", first_name="Zuleyka", last_name="Brown")
        person(username="dd_two", first_name="Zuleyka", last_name="Green")

        self.assertEqual(self.usernames(q="Zuleyka Brown"), ["dd_one"])
        self.assertEqual(self.usernames(q="Brown Zuleyka"), ["dd_one"])

    def test_q_searches_field_by_label_with_partial_word(self):
        person(username="cs_person", field="computer_science")
        person(username="law_person", field="law")

        # метка «Computer Science» → код computer_science; частичное слово тоже находит
        self.assertEqual(self.usernames(q="comput"), ["cs_person"])
        self.assertEqual(self.usernames(q="science"), ["cs_person"])
        self.assertEqual(self.usernames(q="Computer Science"), ["cs_person"])
        self.assertEqual(self.usernames(q="computer_science"), [])  # по коду не ищем
        self.assertEqual(self.usernames(q="la"), ["law_person"])

    def test_q_by_field_label_matches_several_fields(self):
        person(username="civil_eng", field="civil_engineering")
        person(username="mech_eng", field="mechanical_engineering")
        person(username="a_lawyer", field="law")

        self.assertEqual(set(self.usernames(q="engin")), {"civil_eng", "mech_eng"})

    def test_special_characters_are_treated_literally(self):
        # username без «_» и «%»: иначе они совпали бы сами по себе
        person(username="plainone", first_name="Alice", last_name="Smith")
        person(username="percentone", first_name="Per%cent", last_name="Odd")
        person(username="underone", first_name="Un_der", last_name="Odd")

        self.assertEqual(self.usernames(q="%"), ["percentone"])  # не «любой текст»
        self.assertEqual(self.usernames(q="_"), ["underone"])  # не «любой символ»
        self.assertEqual(self.usernames(q="Al%ce"), [])
        for nasty in ("\\", "'", '"', "'; DROP TABLE profiles_profile; --", "%%__", "\x00x"):
            with self.subTest(q=nasty):
                self.assertEqual(self.search(q=nasty).status_code, 200)
        self.assertTrue(Profile.objects.filter(username="plainone").exists())

    def test_q_length_limit(self):
        person(username="somebody_x")

        self.assertEqual(self.search(q="a" * 100).status_code, 200)
        response = self.search(q="a" * 101)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "q"), ["too_long"])

    def test_blank_q_returns_everyone(self):
        person(username="one_x")
        person(username="two_x")

        self.assertEqual(len(self.usernames(q="   ")), 2)


class SearchFilterTests(SearchTestCase):
    def test_each_filter(self):
        person(
            username="match_all",
            country="UZ",
            field="design",
            status="student",
            goals=["mentorship", "friends"],
            languages=["uzbek", "english"],
        )
        person(
            username="match_none",
            country="DE",
            field="law",
            status="professional",
            goals=["startup_cofounders"],
            languages=["german"],
        )

        for params in (
            {"country": "UZ"},
            {"field": "design"},
            {"status": "student"},
            {"goal": "mentorship"},
            {"goal": "friends"},
            {"language": "english"},
        ):
            with self.subTest(params):
                self.assertEqual(self.usernames(**params), ["match_all"])

    def test_filters_combine_with_and(self):
        person(username="both", country="UZ", field="design", status="student")
        person(username="only_country", country="UZ", field="law", status="student")

        self.assertEqual(self.usernames(country="UZ", field="design"), ["both"])
        self.assertEqual(self.usernames(country="UZ", field="design", q="both"), ["both"])
        self.assertEqual(self.usernames(country="UZ", field="design", q="nothing_like_this"), [])

    def test_unknown_filter_codes_are_rejected(self):
        for name in ("country", "field", "status", "goal", "language"):
            with self.subTest(name):
                response = self.search(**{name: "not_a_real_code"})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(field_codes(response, name), ["invalid_choice"])

    def test_empty_filter_values_are_ignored(self):
        person(username="somebody_y")

        self.assertEqual(self.usernames(country="", field="", status="", goal="", language=""), ["somebody_y"])


class SearchOrderAndPagingTests(SearchTestCase):
    def test_newest_first_then_by_id(self):
        now = timezone.now()
        oldest = person(username="oldest_x")
        newest = person(username="newest_x")
        middle = person(username="middle_x")
        Profile.objects.filter(user=oldest).update(created_at=now - timedelta(days=3))
        Profile.objects.filter(user=middle).update(created_at=now - timedelta(days=2))
        Profile.objects.filter(user=newest).update(created_at=now - timedelta(days=1))

        self.assertEqual(self.usernames(), ["newest_x", "middle_x", "oldest_x"])

    def test_same_timestamp_is_ordered_by_id_descending(self):
        stamp = timezone.now() - timedelta(days=1)
        first = person(username="first_x")
        second = person(username="second_x")
        Profile.objects.filter(pk__in=[first.profile.pk, second.profile.pk]).update(created_at=stamp)

        self.assertEqual(self.usernames(), ["second_x", "first_x"])

    def test_default_page_size_is_12_and_pages_work(self):
        for _ in range(14):
            person()

        first = self.search().json()
        second = self.search(page=2).json()

        self.assertEqual((first["count"], len(first["results"])), (14, 12))
        self.assertIsNotNone(first["next"])
        self.assertEqual(len(second["results"]), 2)
        self.assertIsNone(second["next"])
        self.assertEqual(self.search(page=3).status_code, 404)  # за пределами — 404

    def test_page_size_is_capped_at_24(self):
        for _ in range(26):
            person()

        self.assertEqual(len(self.search(page_size=1000).json()["results"]), 24)
        self.assertEqual(len(self.search(page_size=24).json()["results"]), 24)
        self.assertEqual(len(self.search(page_size=5).json()["results"]), 5)

    def test_bad_page_size_falls_back_to_default(self):
        for _ in range(13):
            person()

        for bad in ("0", "abc", "-3"):
            with self.subTest(bad):
                self.assertEqual(len(self.search(page_size=bad).json()["results"]), 12)


@override_settings(THROTTLING_ENABLED=True)
class SearchThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.client.force_login(make_account(email="viewer@example.com", username="viewer"))

    def test_61st_search_in_a_minute_is_throttled(self):
        for _ in range(60):
            self.assertEqual(self.client.get(LIST).status_code, 200)

        response = self.client.get(LIST)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(error_of(response)["code"], "throttled")

    def test_limit_is_per_user(self):
        for _ in range(60):
            self.client.get(LIST)
        other = make_account(email="other@example.com", username="other")
        self.client.force_login(other)

        self.assertEqual(self.client.get(LIST).status_code, 200)


class MinorsInSearchTests(SearchTestCase):
    def test_minor_card_has_no_contacts_or_school(self):
        person(
            username="teen_one",
            date_of_birth=birth_date_for_age(16),
            school="Secret High School",
            show_contacts=True,
        )

        raw = self.search().content.decode()
        card = self.search().json()["results"][0]

        self.assertEqual(card["username"], "teen_one")
        self.assertNotIn("school", card)
        self.assertNotIn("Secret High School", raw)


class SearchCityFilterTests(SearchTestCase):
    """Фильтр city: сравнение с названием из справочника через Lower(Trim(city)), только show_location=True."""

    def test_case_and_edge_spaces_do_not_matter(self):
        for i, text in enumerate(["samarkand", "Samarkand ", "SAMARKAND", " Samarkand", "Samarkand"]):
            person(username=f"sam_{i}", city=text)
        person(username="tash_one", city="Tashkent")

        found = self.usernames(city="samarkand", page_size=24)

        self.assertEqual(set(found), {f"sam_{i}" for i in range(5)})

    def test_hidden_location_is_not_found(self):
        person(username="shown_one", city="Samarkand", show_location=True)
        person(username="hidden_one", city="Samarkand", show_location=False)

        self.assertEqual(self.usernames(city="samarkand"), ["shown_one"])

    def test_unknown_city_code_is_rejected(self):
        for bad in ("atlantis", "Samarkand", "SAMARKAND ", "other", "%", "'; DROP TABLE x; --"):
            with self.subTest(bad):
                response = self.search(city=bad)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(field_codes(response, "city"), ["invalid_choice"])

    def test_empty_city_is_ignored(self):
        person(username="anybody")

        self.assertEqual(self.usernames(city=""), ["anybody"])

    def test_profiles_with_another_city_text_are_not_found_by_the_filter(self):
        person(username="other_city", city="Zomin")  # «Other»: города нет в справочнике
        person(username="in_list", city="Samarkand")

        self.assertEqual(self.usernames(city="samarkand"), ["in_list"])
        self.assertEqual(self.usernames(q="Zomin"), ["other_city"])  # зато находится текстовым поиском

    def test_former_list_city_is_now_other_and_found_only_by_text(self):
        person(username="kokand", city="Kokand")  # был в справочнике из 24 городов, теперь «Other»

        self.assertEqual(self.search(city="kokand").status_code, 400)  # кода больше нет
        self.assertEqual(self.usernames(q="Kokand"), ["kokand"])

    def test_city_combines_with_other_filters(self):
        person(
            username="match_all",
            city="Samarkand",
            country="UZ",
            field="design",
            status="student",
            goals=["mentorship"],
            languages=["uzbek"],
        )
        person(username="wrong_field", city="Samarkand", country="UZ", field="law", status="student",
               goals=["mentorship"], languages=["uzbek"])
        person(username="wrong_city", city="Bukhara", country="UZ", field="design", status="student",
               goals=["mentorship"], languages=["uzbek"])

        self.assertEqual(
            self.usernames(city="samarkand", field="design", status="student", goal="mentorship", language="uzbek"),
            ["match_all"],
        )
        self.assertEqual(self.usernames(city="samarkand", country="UZ", q="match"), ["match_all"])
        self.assertEqual(set(self.usernames(city="samarkand")), {"match_all", "wrong_field"})

    def test_country_filter_still_works(self):
        person(username="uz_one", country="UZ", city="Tashkent")
        person(username="de_one", country="DE", city="Berlin")

        self.assertEqual(self.usernames(country="UZ"), ["uz_one"])

    def test_special_characters_in_stored_city_do_not_act_as_patterns(self):
        person(username="percent_city", city="Samar%and")
        person(username="underscore_city", city="Samar_and")
        person(username="real_city", city="Samarkand")

        self.assertEqual(self.usernames(city="samarkand"), ["real_city"])
        for nasty in ("%", "_", "\\", "'"):
            with self.subTest(nasty):
                self.assertEqual(self.search(q=nasty, city="samarkand").status_code, 200)

    def test_minors_follow_the_same_rules(self):
        person(username="teen_sam", city="Samarkand", date_of_birth=birth_date_for_age(16))
        person(username="teen_hidden", city="Samarkand", date_of_birth=birth_date_for_age(16), show_location=False)

        card = self.search(city="samarkand").json()["results"][0]

        self.assertEqual(card["username"], "teen_sam")
        self.assertNotIn("school", card)
