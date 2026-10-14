from rest_framework.test import APITestCase

from apps.profiles import choices
from apps.profiles.models import Profile
from apps.profiles.tests.factories import birth_date_for_age, make_user
from apps.users.tests.helpers import OWN_KEYS, error_of, field_codes, make_account

ME = "/api/me/"

READ_ONLY = {
    "username": "newname",
    "date_of_birth": "2000-01-01",
    "email": "new@example.com",
    "is_banned": True,
    "created_at": "2020-01-01T00:00:00Z",
    "privacy": {"show_contacts": True},
    # вычисляемые поля ответа тоже нельзя «записать»
    "email_verified": False,
    "age": 30,
    "is_minor": False,
    "avatar_url": "/media/avatars/x.webp",
    "country_label": "Nowhere",
    "field_label": "Nothing",
    "status_label": "Nobody",
}


class MeGetTests(APITestCase):
    def test_requires_login(self):
        response = self.client.get(ME)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(error_of(response)["code"], "not_authenticated")

    def test_returns_exactly_the_own_profile_keys(self):
        user = make_account(city="Tashkent", bio="Hello")
        self.client.force_login(user)

        data = self.client.get(ME).json()

        self.assertEqual(set(data), OWN_KEYS)  # нет phone, field_other, is_banned и т.п.
        for absent in ("phone", "field_other", "is_banned"):
            self.assertNotIn(absent, data)
        self.assertEqual(data["email"], "user@example.com")
        self.assertTrue(data["email_verified"])
        self.assertEqual((data["age"], data["is_minor"]), (25, False))
        self.assertIsNone(data["avatar_url"])
        self.assertEqual(
            (data["country_label"], data["status_label"], data["field_label"]),
            (dict(choices.COUNTRIES)[data["country"]], "Student", dict(choices.FIELDS)[data["field"]]),
        )
        self.assertEqual(
            set(data["contacts"]), {"telegram", "instagram", "whatsapp", "linkedin", "public_email"}
        )
        self.assertEqual(
            data["privacy"],
            {
                "show_location": True,
                "show_university": True,
                "show_contacts": False,
                "show_in_search": True,
                "show_join_date": True,
            },
        )

    def test_account_without_profile_gets_404(self):
        user = make_user(email="staff@example.com")
        self.client.force_login(user)

        response = self.client.get(ME)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(error_of(response)["code"], "not_found")


class MePatchTests(APITestCase):
    def setUp(self):
        self.user = make_account()
        self.client.force_login(self.user)

    def patch(self, **data):
        return self.client.patch(ME, data, format="json")

    def test_allowed_fields_are_updated(self):
        response = self.patch(
            first_name="Maria",
            city="Samarkand",
            bio="Hi there",
            interests=["law", "music"],
            languages=["uzbek"],
            goals=["mentorship"],
            gender="female",
            university="WIUT",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["city"], "Samarkand")
        profile = Profile.objects.get(user=self.user)
        self.assertEqual((profile.first_name, profile.bio, profile.gender), ("Maria", "Hi there", "female"))
        self.assertEqual(profile.interests, ["law", "music"])

    def test_read_only_fields_are_rejected_and_nothing_changes(self):
        before = Profile.objects.values().get(user=self.user)

        for name, value in READ_ONLY.items():
            with self.subTest(field=name):
                response = self.patch(**{name: value})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(error_of(response)["code"], "validation_error")
                self.assertEqual(field_codes(response, name), ["read_only_field"])

        self.assertEqual(Profile.objects.values().get(user=self.user), before)

    def test_read_only_field_blocks_the_whole_request(self):
        response = self.patch(city="Samarkand", username="newname")

        self.assertEqual(response.status_code, 400)
        self.assertNotEqual(Profile.objects.get(user=self.user).city, "Samarkand")

    def test_validation(self):
        self.assertEqual(field_codes(self.patch(country="XX"), "country"), ["invalid_choice"])
        self.assertEqual(field_codes(self.patch(bio="x" * 301), "bio"), ["too_long"])
        self.assertEqual(field_codes(self.patch(first_name="<b>"), "first_name"), ["invalid_characters"])
        self.assertEqual(field_codes(self.patch(city=""), "city"), ["required"])
        codes = choices.codes(choices.GOALS)
        self.assertEqual(field_codes(self.patch(goals=codes[:9]), "goals"), ["too_many"])

    def test_body_must_be_an_object(self):
        response = self.client.patch(ME, [1, 2], format="json")

        self.assertEqual(response.status_code, 400)

    def test_adult_contacts_are_saved_and_merged(self):
        self.patch(contacts={"telegram": "@janedoe", "whatsapp": "+998 90 123 45 67"})
        response = self.patch(contacts={"telegram": "newhandle"})  # whatsapp не трогаем

        self.assertEqual(response.status_code, 200)
        contacts = response.json()["contacts"]
        self.assertEqual(contacts["telegram"], "newhandle")
        self.assertEqual(contacts["whatsapp"], "+998901234567")

    def test_contact_format_errors(self):
        response = self.patch(contacts={"telegram": "ab"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "contacts.telegram"), ["invalid"])


class MePatchMinorTests(APITestCase):
    def setUp(self):
        self.user = make_account(date_of_birth=birth_date_for_age(17))
        self.client.force_login(self.user)

    def test_minor_cannot_save_contacts(self):
        response = self.client.patch(ME, {"contacts": {"telegram": "janedoe"}}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "contacts"), ["not_allowed_for_minors"])
        self.assertEqual(Profile.objects.get(user=self.user).telegram, "")

    def test_minor_can_send_empty_contacts_and_other_fields(self):
        response = self.client.patch(
            ME, {"contacts": {"telegram": ""}, "city": "Samarkand"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_minor"])
        self.assertEqual(response.json()["city"], "Samarkand")


class MePatchArraysTests(APITestCase):
    """Массивы interests / languages / goals: коды из справочника, без повторов, в пределах лимитов."""

    LISTS = {
        "interests": (choices.INTERESTS, 10),
        "languages": (choices.LANGUAGES, 10),
        "goals": (choices.GOALS, 8),
    }

    def setUp(self):
        self.user = make_account()
        self.client.force_login(self.user)

    def patch(self, **data):
        return self.client.patch(ME, data, format="json")

    def test_valid_values_up_to_the_limit_are_saved(self):
        for name, (options, limit) in self.LISTS.items():
            with self.subTest(name):
                values = choices.codes(options)[:limit]
                response = self.patch(**{name: values})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()[name], values)

    def test_empty_list_clears_the_field(self):
        self.patch(interests=["law"])

        self.assertEqual(self.patch(interests=[]).json()["interests"], [])

    def test_unknown_code_is_rejected(self):
        for name in self.LISTS:
            with self.subTest(name):
                response = self.patch(**{name: ["not_a_real_code"]})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(field_codes(response, f"{name}.0"), ["invalid_choice"])

    def test_one_over_the_limit_is_rejected(self):
        for name, (options, limit) in self.LISTS.items():
            with self.subTest(name):
                response = self.patch(**{name: choices.codes(options)[: limit + 1]})
                self.assertEqual(field_codes(response, name), ["too_many"])

    def test_duplicates_are_rejected(self):
        for name, (options, _limit) in self.LISTS.items():
            with self.subTest(name):
                code = choices.codes(options)[0]
                self.assertEqual(field_codes(self.patch(**{name: [code, code]}), name), ["duplicate"])

    def test_not_a_list_is_rejected(self):
        for name in self.LISTS:
            for bad in ("law", {"a": 1}, 5, None):
                with self.subTest(name=name, value=bad):
                    self.assertEqual(self.patch(**{name: bad}).status_code, 400)

    def test_rejected_request_changes_nothing(self):
        self.patch(interests=["law"])

        self.patch(interests=["music"], languages=["bad"])

        self.assertEqual(Profile.objects.get(user=self.user).interests, ["law"])

    def test_unknown_keys_are_ignored(self):
        def snapshot():
            data = Profile.objects.values().get(user=self.user)
            data.pop("updated_at")  # время сохранения меняется при любом PATCH
            return data

        before = snapshot()

        response = self.patch(field_other="Robotics", phone="+998901234567")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("phone", response.json())
        self.assertEqual(snapshot(), before)

    def test_text_limits(self):
        self.assertEqual(self.patch(bio="x" * 300).status_code, 200)
        self.assertEqual(field_codes(self.patch(bio="x" * 301), "bio"), ["too_long"])
        self.assertEqual(field_codes(self.patch(year_level="x" * 41), "year_level"), ["too_long"])
        self.assertEqual(field_codes(self.patch(university="x" * 121), "university"), ["too_long"])
        self.assertEqual(field_codes(self.patch(field="not_a_field"), "field"), ["invalid_choice"])
        self.assertEqual(self.patch(field="other").status_code, 200)  # «Other» — обычный код без текста

    def test_requires_login(self):
        self.client.logout()

        self.assertEqual(self.patch(city="X").status_code, 401)
