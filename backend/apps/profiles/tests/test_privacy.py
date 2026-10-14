from rest_framework.test import APITestCase

from apps.profiles.models import Profile
from apps.profiles.tests.factories import birth_date_for_age, make_user
from apps.users.tests.helpers import error_of, field_codes, make_account

PRIVACY = "/api/me/privacy/"
FLAGS = ("show_location", "show_university", "show_contacts", "show_in_search", "show_join_date")
DEFAULTS = {
    "show_location": True,
    "show_university": True,
    "show_contacts": False,
    "show_in_search": True,
    "show_join_date": True,
}


class PrivacyTests(APITestCase):
    def setUp(self):
        self.user = make_account()
        self.client.force_login(self.user)

    def patch(self, **data):
        return self.client.patch(PRIVACY, data, format="json")

    def test_requires_login(self):
        self.client.logout()

        for response in (self.client.get(PRIVACY), self.patch(show_location=False)):
            self.assertEqual(response.status_code, 401)
            self.assertEqual(error_of(response)["code"], "not_authenticated")

    def test_get_returns_the_five_flags(self):
        response = self.client.get(PRIVACY)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), DEFAULTS)

    def test_each_flag_can_be_changed_alone(self):
        for name in FLAGS:
            with self.subTest(name):
                new_value = not DEFAULTS[name]
                response = self.patch(**{name: new_value})
                self.assertEqual(response.status_code, 200)
                expected = {**DEFAULTS, name: new_value}
                self.assertEqual(response.json(), expected)
                self.assertEqual(self.client.get(PRIVACY).json(), expected)
                self.patch(**{name: DEFAULTS[name]})  # возвращаем

    def test_several_flags_at_once_and_empty_body(self):
        response = self.patch(show_location=False, show_in_search=False)

        self.assertEqual(response.json()["show_location"], False)
        self.assertEqual(response.json()["show_in_search"], False)
        self.assertEqual(response.json()["show_university"], True)  # остальные не тронуты
        self.assertEqual(self.patch().status_code, 200)

    def test_values_are_visible_in_me(self):
        self.patch(show_join_date=False)

        self.assertFalse(self.client.get("/api/me/").json()["privacy"]["show_join_date"])

    def test_adult_can_enable_contacts(self):
        response = self.patch(show_contacts=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["show_contacts"])

    def test_non_boolean_value_is_rejected(self):
        response = self.patch(show_location="maybe")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "show_location"), ["invalid"])

    def test_body_must_be_an_object(self):
        self.assertEqual(self.client.patch(PRIVACY, [True], format="json").status_code, 400)

    def test_account_without_profile_gets_404(self):
        self.client.force_login(make_user(email="staff@example.com"))

        self.assertEqual(self.client.get(PRIVACY).status_code, 404)

    def test_other_methods_are_not_allowed(self):
        self.assertEqual(self.client.post(PRIVACY, {}, format="json").status_code, 405)
        self.assertEqual(self.client.delete(PRIVACY).status_code, 405)


class PrivacyMinorTests(APITestCase):
    def setUp(self):
        self.user = make_account(date_of_birth=birth_date_for_age(17))
        self.client.force_login(self.user)

    def test_show_contacts_true_is_rejected_and_not_saved(self):
        response = self.client.patch(PRIVACY, {"show_contacts": True}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "show_contacts"), ["not_allowed_for_minors"])
        self.assertFalse(Profile.objects.get(user=self.user).show_contacts)

    def test_show_contacts_false_is_fine_and_other_flags_work(self):
        response = self.client.patch(
            PRIVACY, {"show_contacts": False, "show_location": False}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["show_location"], False)
        self.assertEqual(response.json()["show_contacts"], False)

    def test_rejected_request_changes_nothing(self):
        self.client.patch(PRIVACY, {"show_contacts": True, "show_location": False}, format="json")

        self.assertTrue(Profile.objects.get(user=self.user).show_location)

    def test_minor_always_sees_contacts_hidden(self):
        Profile.objects.filter(user=self.user).update(show_contacts=True)  # запись в обход API

        self.assertFalse(self.client.get(PRIVACY).json()["show_contacts"])
        self.assertFalse(self.client.get("/api/me/").json()["privacy"]["show_contacts"])

    def test_age_boundary_18_can_enable(self):
        adult = make_account(email="adult@example.com", date_of_birth=birth_date_for_age(18))
        self.client.force_login(adult)

        response = self.client.patch(PRIVACY, {"show_contacts": True}, format="json")

        self.assertEqual(response.status_code, 200)
