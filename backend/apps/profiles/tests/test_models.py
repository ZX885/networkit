from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.profiles import choices
from apps.profiles.models import Profile
from apps.profiles.validators import RESERVED_USERNAMES

from .factories import birth_date_for_age, make_profile, make_user


class ProfileTestCase(TestCase):
    def assert_invalid(self, profile, field, code=None):
        """full_clean() должен отклонить профиль с ошибкой в поле field."""
        with self.assertRaises(ValidationError) as context:
            profile.full_clean()
        self.assertIn(field, context.exception.message_dict)
        if code:
            codes = [e.code for e in context.exception.error_dict[field]]
            self.assertIn(code, codes)

    def assert_valid(self, profile):
        profile.full_clean()  # не должен бросать исключение


class ProfileDefaultsTests(ProfileTestCase):
    def test_privacy_flags_defaults(self):
        profile = make_profile()

        self.assertTrue(profile.show_location)
        self.assertTrue(profile.show_university)
        self.assertFalse(profile.show_contacts)  # контакты скрыты, пока человек сам не откроет
        self.assertTrue(profile.show_in_search)
        self.assertTrue(profile.show_join_date)

    def test_valid_profile_passes_full_clean(self):
        self.assert_valid(make_profile())

    def test_lists_default_to_empty(self):
        profile = make_profile()

        self.assertEqual(profile.interests, [])
        self.assertEqual(profile.languages, [])
        self.assertEqual(profile.goals, [])

    def test_one_profile_per_user(self):
        user = make_user()
        make_profile(user=user)

        with self.assertRaises(IntegrityError), transaction.atomic():
            make_profile(user=user)


class UsernameTests(ProfileTestCase):
    def test_invalid_usernames_are_rejected(self):
        invalid = {
            "Jane": "uppercase letter",
            "jane doe": "space",
            "jane__doe": "double underscore",
            "ab": "too short",
            "1jane": "starts with a digit",
            "jane-doe": "hyphen",
            "a" * 31: "too long",
        }
        for username, reason in invalid.items():
            with self.subTest(reason=reason):
                profile = make_profile()
                profile.username = username
                self.assert_invalid(profile, "username")

    def test_reserved_usernames_are_rejected(self):
        for username in sorted(RESERVED_USERNAMES):
            with self.subTest(username=username):
                profile = make_profile()
                profile.username = username
                self.assert_invalid(profile, "username")

    def test_reserved_username_with_valid_format_gets_reserved_code(self):
        # «me» короче 3 символов и отклоняется по формату; остальные доходят до проверки «reserved»
        profile = make_profile()
        profile.username = "admin"

        self.assert_invalid(profile, "username", code="reserved")

    def test_valid_usernames_pass(self):
        for username in ["jane", "jane_doe", "a_b", "user123", "a" * 30]:
            with self.subTest(username=username):
                profile = make_profile()
                profile.username = username
                self.assert_valid(profile)

    def test_username_is_unique(self):
        make_profile(username="janedoe")

        with self.assertRaises(IntegrityError), transaction.atomic():
            make_profile(username="janedoe")

    def test_database_rejects_bad_username_even_without_validation(self):
        profile = make_profile()

        for bad in ["Jane", "jane__doe", "ab"]:
            with self.subTest(username=bad), self.assertRaises(IntegrityError), transaction.atomic():
                Profile.objects.filter(pk=profile.pk).update(username=bad)


class BioAndChoicesTests(ProfileTestCase):
    def test_bio_300_is_ok_and_301_is_rejected(self):
        profile = make_profile()

        profile.bio = "x" * 300
        self.assert_valid(profile)
        profile.bio = "x" * 301
        self.assert_invalid(profile, "bio")

    def test_database_rejects_long_bio_without_validation(self):
        profile = make_profile()

        with self.assertRaises(IntegrityError), transaction.atomic():
            Profile.objects.filter(pk=profile.pk).update(bio="x" * 301)

    def test_unknown_choice_codes_are_rejected(self):
        cases = {
            "country": "XX",
            "field": "astrology",
            "status": "retired",
            "gender": "other_gender",
        }
        for field, bad_value in cases.items():
            with self.subTest(field=field):
                profile = make_profile()
                setattr(profile, field, bad_value)
                self.assert_invalid(profile, field, code="invalid_choice")

    def test_all_declared_codes_are_accepted(self):
        profile = make_profile()
        for country in choices.codes(choices.COUNTRIES):
            profile.country = country
            profile.full_clean()
        for field in choices.codes(choices.FIELDS):
            profile.field = field
            profile.full_clean()

    def test_gender_is_optional(self):
        profile = make_profile(gender="")

        self.assert_valid(profile)

    def test_field_other_is_a_valid_code(self):
        self.assertIn("other", choices.codes(choices.FIELDS))
        self.assert_valid(make_profile(field="other"))


class ListLimitTests(ProfileTestCase):
    def test_limits_10_10_8(self):
        # (поле, справочник, максимум)
        cases = [
            ("interests", choices.INTERESTS, 10),
            ("languages", choices.LANGUAGES, 10),
            ("goals", choices.GOALS, 8),
        ]
        for field, catalog, limit in cases:
            codes = choices.codes(catalog)
            with self.subTest(field=field, size=limit):
                profile = make_profile()
                setattr(profile, field, codes[:limit])
                self.assert_valid(profile)
            with self.subTest(field=field, size=limit + 1):
                profile = make_profile()
                setattr(profile, field, codes[: limit + 1])
                self.assert_invalid(profile, field)

    def test_unknown_code_in_list_is_rejected(self):
        for field in ["interests", "languages", "goals"]:
            with self.subTest(field=field):
                profile = make_profile()
                setattr(profile, field, ["no_such_code"])
                self.assert_invalid(profile, field)

    def test_duplicates_in_list_are_rejected(self):
        profile = make_profile()
        profile.interests = ["law", "law"]

        self.assert_invalid(profile, "interests", code="duplicate")

    def test_database_rejects_oversized_lists_without_validation(self):
        profile = make_profile()
        cases = [
            ("interests", choices.codes(choices.INTERESTS)[:11]),
            ("languages", choices.codes(choices.LANGUAGES)[:11]),
            ("goals", choices.codes(choices.GOALS)[:9]),
        ]
        for field, too_many in cases:
            with self.subTest(field=field), self.assertRaises(IntegrityError), transaction.atomic():
                Profile.objects.filter(pk=profile.pk).update(**{field: too_many})


class DateOfBirthTests(ProfileTestCase):
    def test_min_age_boundary(self):
        profile = make_profile()

        profile.date_of_birth = birth_date_for_age(13)  # сегодня исполнилось 13
        self.assert_valid(profile)
        profile.date_of_birth = birth_date_for_age(13, days_short=1)  # до 13-летия 1 день
        self.assert_invalid(profile, "date_of_birth", code="too_young")

    def test_max_age_boundary(self):
        profile = make_profile()

        profile.date_of_birth = birth_date_for_age(100)
        self.assert_valid(profile)
        profile.date_of_birth = birth_date_for_age(101)
        self.assert_invalid(profile, "date_of_birth", code="too_old")

    def test_future_date_is_rejected(self):
        profile = make_profile()
        profile.date_of_birth = date.today() + timedelta(days=1)

        self.assert_invalid(profile, "date_of_birth", code="future")


class AgeTests(ProfileTestCase):
    # Дата рождения 15 июня 2000 года
    def profile(self):
        return make_profile(date_of_birth=date(2000, 6, 15))

    def test_age_on_13th_birthday_boundary(self):
        profile = self.profile()

        self.assertEqual(profile.age(today=date(2013, 6, 14)), 12)
        self.assertEqual(profile.age(today=date(2013, 6, 15)), 13)

    def test_17_is_minor_and_18_is_not(self):
        profile = self.profile()

        eve = date(2018, 6, 14)  # накануне 18-летия
        birthday = date(2018, 6, 15)  # исполнилось 18
        self.assertEqual(profile.age(today=eve), 17)
        self.assertTrue(profile.is_minor(today=eve))
        self.assertEqual(profile.age(today=birthday), 18)
        self.assertFalse(profile.is_minor(today=birthday))

    def test_13_year_old_is_minor(self):
        profile = self.profile()

        self.assertTrue(profile.is_minor(today=date(2013, 6, 15)))

    def test_leap_day_birthday(self):
        profile = make_profile(date_of_birth=date(2004, 2, 29))

        self.assertEqual(profile.age(today=date(2022, 2, 28)), 17)
        self.assertEqual(profile.age(today=date(2022, 3, 1)), 18)

    def test_age_defaults_to_today(self):
        profile = make_profile(date_of_birth=birth_date_for_age(30))

        self.assertEqual(profile.age(), 30)
        self.assertFalse(profile.is_minor())


class MinorContactsTests(ProfileTestCase):
    CONTACTS = {
        "telegram": "janedoe",
        "instagram": "janedoe",
        "whatsapp": "+998901234567",
        "linkedin": "https://linkedin.com/in/janedoe",
        "public_email": "jane@example.com",
    }

    def minor(self, **overrides):
        return make_profile(date_of_birth=birth_date_for_age(17), **overrides)

    def test_minor_cannot_have_any_contact(self):
        for field, value in self.CONTACTS.items():
            with self.subTest(field=field):
                profile = self.minor()
                setattr(profile, field, value)
                self.assert_invalid(profile, field, code="not_allowed_for_minors")

    def test_minor_cannot_enable_show_contacts(self):
        profile = self.minor()
        profile.show_contacts = True

        self.assert_invalid(profile, "show_contacts", code="not_allowed_for_minors")

    def test_minor_without_contacts_is_valid(self):
        self.assert_valid(self.minor())

    def test_adult_may_have_contacts_and_show_them(self):
        profile = make_profile(date_of_birth=birth_date_for_age(18), **self.CONTACTS)
        profile.show_contacts = True

        self.assert_valid(profile)

    def test_17_year_old_turning_18_today_is_adult(self):
        profile = make_profile(date_of_birth=birth_date_for_age(18), telegram="janedoe")

        self.assert_valid(profile)

    def test_day_before_18th_birthday_is_still_minor(self):
        profile = make_profile(
            date_of_birth=birth_date_for_age(18, days_short=1), telegram="janedoe"
        )

        self.assert_invalid(profile, "telegram", code="not_allowed_for_minors")
