from rest_framework.test import APITestCase

from apps.profiles.models import Profile
from apps.profiles.tests.factories import birth_date_for_age
from apps.users.models import User
from apps.users.tests.helpers import error_of, make_account

PUBLIC_KEYS = {
    "username",
    "first_name",
    "last_name",
    "avatar_url",
    "field",
    "field_label",
    "status",
    "status_label",
    "city",
    "region",
    "country",
    "country_label",
    "bio",
    "interests",
    "is_saved",
    "school",
    "university",
    "year_level",
    "languages",
    "goals",
    "contacts",
    "joined",
}


def url(username):
    return f"/api/profiles/{username}/"


class PublicProfileTestCase(APITestCase):
    def setUp(self):
        self.viewer = make_account(email="viewer@example.com", username="viewer")
        self.client.force_login(self.viewer)

    def other(self, **profile):
        profile.setdefault("username", "maria")
        return make_account(email="maria@example.com", **profile)


class PublicProfileAccessTests(PublicProfileTestCase):
    def test_requires_login(self):
        self.other()
        self.client.logout()

        response = self.client.get(url("maria"))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(error_of(response)["code"], "not_authenticated")

    def test_unknown_user_is_404(self):
        response = self.client.get(url("nobody_here"))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(error_of(response)["code"], "not_found")

    def test_banned_inactive_and_unverified_are_404(self):
        banned = self.other(username="banned_one")
        User.objects.filter(pk=banned.pk).update(is_banned=True)
        make_account(email="unv@example.com", verified=False, username="unverified")
        inactive = make_account(email="inact@example.com", username="inactive_one")
        User.objects.filter(pk=inactive.pk).update(is_active=False)

        for name in ("banned_one", "unverified", "inactive_one"):
            with self.subTest(name):
                self.assertEqual(self.client.get(url(name)).status_code, 404)

    def test_profile_hidden_from_search_opens_by_direct_link(self):
        self.other(show_in_search=False)

        self.assertEqual(self.client.get(url("maria")).status_code, 200)

    def test_own_profile_can_be_opened(self):
        response = self.client.get(url("viewer"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "viewer")

    def test_username_is_case_insensitive(self):
        self.other()

        self.assertEqual(self.client.get(url("MARIA")).status_code, 200)

    def test_only_get_is_allowed(self):
        self.other()

        self.assertEqual(self.client.post(url("maria"), {}, format="json").status_code, 405)
        self.assertEqual(self.client.patch(url("maria"), {}, format="json").status_code, 405)


class PublicProfileContentTests(PublicProfileTestCase):
    def test_exact_keys_and_no_private_data(self):
        self.other(gender="female", telegram="maria_tg", show_contacts=False)

        response = self.client.get(url("maria"))
        data = response.json()
        raw = response.content.decode()

        self.assertEqual(set(data), PUBLIC_KEYS)
        for forbidden in (
            "email",
            "date_of_birth",
            "is_banned",
            "phone",
            "gender",
            "privacy",
            "maria_tg",
            "example.com",
            '"age"',
            "show_",
        ):
            self.assertNotIn(forbidden, raw)

    def test_visible_fields(self):
        self.other(
            city="Samarkand",
            region="Samarkand region",
            country="UZ",
            university="WIUT",
            school="Lyceum 5",
            year_level="2nd year",
            bio="Hello",
            interests=["law"],
            languages=["uzbek"],
            goals=["mentorship"],
        )

        data = self.client.get(url("maria")).json()

        self.assertEqual(
            (data["city"], data["region"], data["country"], data["country_label"]),
            ("Samarkand", "Samarkand region", "UZ", "Uzbekistan"),
        )
        self.assertEqual((data["university"], data["school"]), ("WIUT", "Lyceum 5"))
        self.assertEqual(
            (data["year_level"], data["interests"], data["languages"], data["goals"]),
            ("2nd year", ["law"], ["uzbek"], ["mentorship"]),
        )
        self.assertRegex(data["joined"], r"^\d{4}-\d{2}$")
        self.assertFalse(data["is_saved"])
        self.assertIsNone(data["avatar_url"])

    def test_hidden_fields_are_null_not_missing(self):
        self.other(show_location=False, show_university=False, show_join_date=False)

        data = self.client.get(url("maria")).json()

        for key in ("city", "region", "country", "country_label", "university", "joined", "contacts"):
            self.assertIn(key, data)
            self.assertIsNone(data[key], key)

    def test_adult_contacts_only_when_enabled(self):
        self.other(telegram="maria_tg", public_email="m@example.org", show_contacts=True)

        contacts = self.client.get(url("maria")).json()["contacts"]

        self.assertEqual(set(contacts), {"telegram", "instagram", "whatsapp", "linkedin", "public_email"})
        self.assertEqual((contacts["telegram"], contacts["public_email"]), ("maria_tg", "m@example.org"))

        Profile.objects.filter(username="maria").update(show_contacts=False)
        self.assertIsNone(self.client.get(url("maria")).json()["contacts"])


class PublicProfileMinorTests(PublicProfileTestCase):
    def teen(self, **profile):
        defaults = {
            "username": "teen_one",
            "date_of_birth": birth_date_for_age(16),
            "school": "Secret High School",
        }
        defaults.update(profile)
        return make_account(email="teen@example.com", **defaults)

    def test_contacts_are_null_for_a_minor_even_if_show_contacts_is_true(self):
        self.teen()
        # Запись в обход API и модели: как если бы флаг и контакты остались от прошлых данных
        Profile.objects.filter(username="teen_one").update(
            show_contacts=True, telegram="teen_tg", public_email="teen@example.org"
        )

        response = self.client.get(url("teen_one"))

        self.assertIsNone(response.json()["contacts"])
        self.assertNotIn("teen_tg", response.content.decode())
        self.assertNotIn("teen@example.org", response.content.decode())

    def test_school_is_null_for_a_minor_but_visible_for_an_adult(self):
        self.teen()
        self.other(school="Lyceum 5")

        self.assertIsNone(self.client.get(url("teen_one")).json()["school"])
        self.assertNotIn("Secret High School", self.client.get(url("teen_one")).content.decode())
        self.assertEqual(self.client.get(url("maria")).json()["school"], "Lyceum 5")

    def test_a_person_who_just_turned_18_gets_adult_rules(self):
        self.teen(date_of_birth=birth_date_for_age(18), username="eighteen")
        Profile.objects.filter(username="eighteen").update(show_contacts=True, telegram="adult_tg")

        data = self.client.get(url("eighteen")).json()

        self.assertEqual(data["school"], "Secret High School")
        self.assertEqual(data["contacts"]["telegram"], "adult_tg")

    def test_a_person_one_day_short_of_18_is_still_a_minor(self):
        self.teen(date_of_birth=birth_date_for_age(18, days_short=1), username="almost")
        Profile.objects.filter(username="almost").update(show_contacts=True, telegram="almost_tg")

        data = self.client.get(url("almost")).json()

        self.assertIsNone(data["school"])
        self.assertIsNone(data["contacts"])
