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
        self.assertEqual(data["email"], "user@example.com")
        self.assertTrue(data["email_verified"])
        self.assertEqual((data["age"], data["is_minor"]), (25, False))
        self.assertIsNone(data["avatar_url"])
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
