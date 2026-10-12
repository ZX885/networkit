from unittest import mock

from django.core import mail
from django.db import IntegrityError
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.profiles.models import Profile
from apps.profiles.tests.factories import birth_date_for_age
from apps.users.models import User

from .helpers import PASSWORD, error_of, field_codes, make_account, registration_payload

URL = "/api/auth/register/"


class RegistrationTests(APITestCase):
    def register(self, **overrides):
        return self.client.post(URL, registration_payload(**overrides), format="json")

    def test_creates_user_and_profile_and_sends_email(self):
        response = self.register()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"status": "verification_sent", "email": "jane@example.com"})
        user = User.objects.get(email="jane@example.com")
        self.assertIsNone(user.email_verified_at)  # почта ещё не подтверждена
        self.assertTrue(user.check_password(PASSWORD))
        profile = user.profile
        self.assertEqual((profile.username, profile.country, profile.field), ("janedoe", "UZ", "computer_science"))
        # Приватность по умолчанию: город виден, контакты скрыты
        self.assertTrue(profile.show_location)
        self.assertFalse(profile.show_contacts)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["jane@example.com"])
        self.assertIn("/verify-email/", mail.outbox[0].body)

    def test_email_and_username_are_normalized(self):
        self.register(email="  Jane@Example.COM ", username="JaneDoe")

        user = User.objects.get(email="jane@example.com")
        self.assertEqual(user.profile.username, "janedoe")

    def test_unknown_keys_are_ignored(self):
        response = self.register(phone="+998901234567", field_other="Archaeology")

        self.assertEqual(response.status_code, 201)
        self.assertFalse(hasattr(Profile, "phone"))

    def test_atomic_user_is_not_left_without_profile(self):
        with mock.patch.object(Profile.objects, "create", side_effect=IntegrityError):
            response = self.register()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "username"), ["taken"])
        self.assertEqual(User.objects.count(), 0)


class DuplicateEmailTests(APITestCase):
    def test_verified_email_creates_no_second_account_and_same_response(self):
        make_account(email="jane@example.com", username="someone")
        fresh = self.client.post(URL, registration_payload(email="new@example.com"), format="json")
        mail.outbox.clear()

        response = self.client.post(URL, registration_payload(username="another"), format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"status": "verification_sent", "email": "jane@example.com"})
        self.assertEqual(fresh.status_code, response.status_code)
        self.assertEqual(User.objects.filter(email="jane@example.com").count(), 1)
        self.assertFalse(Profile.objects.filter(username="another").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("already have", mail.outbox[0].subject)

    def test_email_in_other_case_is_the_same_account(self):
        make_account(email="jane@example.com", username="someone")

        response = self.client.post(URL, registration_payload(email="JANE@example.com"), format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 1)

    def test_unverified_email_gets_verification_mail_again(self):
        make_account(email="jane@example.com", verified=False, username="someone")

        response = self.client.post(URL, registration_payload(username="another"), format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/verify-email/", mail.outbox[0].body)


class AgeTests(APITestCase):
    def register(self, birth_date):
        return self.client.post(
            URL, registration_payload(date_of_birth=birth_date.isoformat()), format="json"
        )

    def test_12_years_old_is_rejected(self):
        response = self.register(birth_date_for_age(12))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "date_of_birth"), ["too_young"])
        self.assertEqual(User.objects.count(), 0)

    def test_day_before_13th_birthday_is_rejected(self):
        response = self.register(birth_date_for_age(13, days_short=1))

        self.assertEqual(field_codes(response, "date_of_birth"), ["too_young"])

    def test_exactly_13_is_accepted(self):
        response = self.register(birth_date_for_age(13))

        self.assertEqual(response.status_code, 201)

    def test_future_date_and_over_100_are_rejected(self):
        future = self.register(birth_date_for_age(-1))
        old = self.register(birth_date_for_age(101))

        self.assertEqual(field_codes(future, "date_of_birth"), ["future"])
        self.assertEqual(field_codes(old, "date_of_birth"), ["too_old"])

    def test_invalid_date_format_is_rejected(self):
        response = self.client.post(URL, registration_payload(date_of_birth="31.02.2000"), format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "date_of_birth"), ["invalid"])


class MinorContactsTests(APITestCase):
    CONTACTS = {"telegram": "janedoe", "whatsapp": "+998901234567"}

    def test_17_year_old_cannot_have_contacts(self):
        response = self.client.post(
            URL,
            registration_payload(date_of_birth=birth_date_for_age(17).isoformat(), contacts=self.CONTACTS),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "contacts"), ["not_allowed_for_minors"])
        self.assertEqual(User.objects.count(), 0)

    def test_17_year_old_with_empty_contacts_is_fine(self):
        blank = {"telegram": "", "instagram": "", "whatsapp": "", "linkedin": "", "public_email": ""}
        response = self.client.post(
            URL,
            registration_payload(date_of_birth=birth_date_for_age(17).isoformat(), contacts=blank),
            format="json",
        )

        self.assertEqual(response.status_code, 201)

    def test_adult_contacts_are_saved_normalized(self):
        contacts = {
            "telegram": "@janedoe",
            "instagram": "@jane.doe",
            "whatsapp": "+998 90 123 45 67",
            "linkedin": "linkedin.com/in/jane-doe",
            "public_email": "jane@work.com",
        }
        response = self.client.post(
            URL,
            registration_payload(date_of_birth=birth_date_for_age(18).isoformat(), contacts=contacts),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        profile = Profile.objects.get(username="janedoe")
        self.assertEqual(profile.telegram, "janedoe")
        self.assertEqual(profile.instagram, "jane.doe")
        self.assertEqual(profile.whatsapp, "+998901234567")
        self.assertEqual(profile.linkedin, "https://www.linkedin.com/in/jane-doe")
        self.assertFalse(profile.show_contacts)  # сами контакты не открываются без решения человека

    def test_contact_formats_are_checked(self):
        contacts = {
            "telegram": "ab",
            "instagram": "bad name!",
            "whatsapp": "12345",
            "linkedin": "https://evil.example.com/in/jane",
            "public_email": "nope",
        }
        response = self.client.post(URL, registration_payload(contacts=contacts), format="json")

        self.assertEqual(response.status_code, 400)
        for name in contacts:
            self.assertEqual(field_codes(response, f"contacts.{name}"), ["invalid"], name)


class UsernameTests(APITestCase):
    def register_with(self, username):
        return self.client.post(URL, registration_payload(username=username), format="json")

    def test_invalid_usernames_are_rejected(self):
        for username in ["ab", "jane doe", "a__b", "1abc", "jane-doe", "a" * 31]:
            with self.subTest(username=username):
                response = self.register_with(username)
                self.assertEqual(response.status_code, 400)
                self.assertIn("username", error_of(response)["fields"])

    def test_reserved_usernames_are_rejected(self):
        for username in ["admin", "api", "support", "networkit"]:
            with self.subTest(username=username):
                self.assertEqual(field_codes(self.register_with(username), "username"), ["reserved"])

    def test_taken_username_is_rejected(self):
        make_account(email="other@example.com", username="janedoe")

        response = self.register_with("JaneDoe")  # регистр не важен

        self.assertEqual(field_codes(response, "username"), ["taken"])

    def test_username_availability_endpoint(self):
        make_account(username="taken_name")
        url = "/api/auth/username-available/"
        cases = {
            "free_name": {"available": True},
            "Free_Name": {"available": True},
            "taken_name": {"available": False, "reason": "taken"},
            "ab": {"available": False, "reason": "invalid_format"},
            "a__b": {"available": False, "reason": "invalid_format"},
            "admin": {"available": False, "reason": "reserved"},
            "": {"available": False, "reason": "invalid_format"},
        }
        for username, expected in cases.items():
            with self.subTest(username=username):
                response = self.client.get(url, {"username": username})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), expected)


class PasswordTests(APITestCase):
    def codes_for(self, password, **overrides):
        response = self.client.post(URL, registration_payload(password=password, **overrides), format="json")
        self.assertEqual(response.status_code, 400, password)
        return field_codes(response, "password")

    def test_too_short(self):
        self.assertIn("too_short", self.codes_for("abc12"))

    def test_only_digits(self):
        self.assertIn("entirely_numeric", self.codes_for("48172635"))

    def test_common_password(self):
        self.assertIn("too_common", self.codes_for("password"))

    def test_too_similar_to_email(self):
        self.assertIn("too_similar", self.codes_for("janedoe123", email="janedoe@example.com"))

    def test_strong_password_is_accepted(self):
        response = self.client.post(URL, registration_payload(password="Tr0ub4dor&3-horse"), format="json")

        self.assertEqual(response.status_code, 201)


class ProfileFieldsTests(APITestCase):
    def post(self, **overrides):
        return self.client.post(URL, registration_payload(**overrides), format="json")

    def test_terms_are_required(self):
        self.assertEqual(field_codes(self.post(accepted_terms=False), "accepted_terms"), ["required"])
        data = registration_payload()
        del data["accepted_terms"]
        response = self.client.post(URL, data, format="json")
        self.assertEqual(field_codes(response, "accepted_terms"), ["required"])

    def test_unknown_choice_codes(self):
        for field, value in {"country": "XX", "field": "astrology", "status": "retired", "gender": "x"}.items():
            with self.subTest(field=field):
                self.assertEqual(field_codes(self.post(**{field: value}), field), ["invalid_choice"])

    def test_list_limits_duplicates_and_unknown_codes(self):
        response = self.post(
            interests=["law"] * 2, languages=["no_such_language"], goals=["friends"] * 9
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(field_codes(response, "interests"), ["duplicate"])
        self.assertTrue(any(key.startswith("languages") for key in error_of(response)["fields"]))
        self.assertIn("too_many", field_codes(response, "goals"))

    def test_eleven_interests_are_too_many(self):
        from apps.profiles import choices

        codes = choices.codes(choices.INTERESTS)
        self.assertEqual(self.post(interests=codes[:11]).status_code, 400)
        self.assertEqual(self.post(interests=codes[:10]).status_code, 201)

    def test_bio_limit(self):
        self.assertEqual(field_codes(self.post(bio="x" * 301), "bio"), ["too_long"])

    def test_names(self):
        self.assertEqual(field_codes(self.post(first_name="<script>"), "first_name"), ["invalid_characters"])
        self.assertEqual(field_codes(self.post(first_name=""), "first_name"), ["required"])
        self.assertEqual(self.post(first_name="Mary-Jane", last_name="O'Neil").status_code, 201)

    def test_required_fields_are_reported_together(self):
        response = self.client.post(URL, {}, format="json")

        self.assertEqual(response.status_code, 400)
        missing = set(error_of(response)["fields"])
        self.assertTrue(
            {"email", "password", "username", "first_name", "last_name", "date_of_birth", "country", "city",
             "status", "field", "accepted_terms"} <= missing
        )


@override_settings(THROTTLING_ENABLED=True)
class RegisterThrottleTests(APITestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    def test_sixth_registration_in_an_hour_is_throttled(self):
        for i in range(5):
            payload = registration_payload(email=f"user{i}@example.com", username=f"person{i}")
            self.assertEqual(self.client.post(URL, payload, format="json").status_code, 201)

        response = self.client.post(URL, registration_payload(email="late@example.com"), format="json")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(error_of(response)["code"], "throttled")
