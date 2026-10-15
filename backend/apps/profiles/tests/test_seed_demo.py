from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.profiles.models import Profile
from apps.users.models import User
from apps.users.tests.helpers import make_account

FLAG = "--i-know-this-is-a-demo"


def seed(*args):
    out = StringIO()
    call_command("seed_demo_profiles", *args, stdout=out)
    return out.getvalue()


def demo_users():
    return User.objects.filter(email__regex=r"^demo-[0-9]+@example\.invalid$")


class SeedGuardTests(TestCase):
    """Тесты Django идут с DEBUG=False: без флага команда не должна ничего делать."""

    def test_refuses_without_flag_when_debug_is_off(self):
        with self.assertRaises(CommandError) as raised:
            seed("--count", "3")

        self.assertIn(FLAG, str(raised.exception))
        self.assertEqual(User.objects.count(), 0)

    def test_delete_is_also_refused_without_flag(self):
        make_account(email="demo-1@example.invalid", username="demo_one")

        with self.assertRaises(CommandError):
            seed("--delete")

        self.assertEqual(demo_users().count(), 1)

    def test_works_with_the_flag(self):
        seed("--count", "3", FLAG)

        self.assertEqual(demo_users().count(), 3)

    @override_settings(DEBUG=True)
    def test_works_in_debug_without_the_flag(self):
        seed("--count", "2")

        self.assertEqual(demo_users().count(), 2)

    def test_count_must_be_positive(self):
        with self.assertRaises(CommandError):
            seed("--count", "0", FLAG)


class SeedDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed("--count", "40", FLAG)

    def test_creates_verified_users_with_unusable_passwords(self):
        users = list(demo_users())

        self.assertEqual(len(users), 40)
        for user in users:
            self.assertTrue(user.email.endswith("@example.invalid"))
            self.assertIsNotNone(user.email_verified_at)
            self.assertFalse(user.has_usable_password())
            self.assertFalse(user.is_staff or user.is_superuser or user.is_banned)
            self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_some_are_minors_and_they_have_no_contacts(self):
        minors = [p for p in Profile.objects.all() if p.is_minor()]

        self.assertGreaterEqual(len(minors), 4)
        for profile in minors:
            self.assertFalse(profile.show_contacts)
            for name in ("telegram", "instagram", "whatsapp", "linkedin", "public_email"):
                self.assertEqual(getattr(profile, name), "", f"{profile.username}.{name}")
            self.assertTrue(profile.school)  # школа есть в данных, но наружу у несовершеннолетних не уходит

    def test_there_is_variety_of_privacy_settings(self):
        profiles = Profile.objects.all()

        self.assertTrue(any(not p.show_location for p in profiles))
        self.assertTrue(any(not p.show_university for p in profiles))
        self.assertTrue(any(not p.show_in_search for p in profiles))
        self.assertTrue(any(p.show_contacts for p in profiles))
        self.assertTrue(any(p.is_minor() for p in profiles) and any(not p.is_minor() for p in profiles))

    def test_all_profiles_are_valid_and_have_unique_usernames(self):
        usernames = list(Profile.objects.values_list("username", flat=True))

        self.assertEqual(len(usernames), len(set(usernames)))
        for profile in Profile.objects.all():
            profile.full_clean()

    def test_fictional_data_only(self):
        for profile in Profile.objects.all():
            self.assertTrue(profile.user.email.endswith("@example.invalid"))
            if profile.public_email:
                self.assertTrue(profile.public_email.endswith("@example.invalid"))


class SeedRepeatAndDeleteTests(TestCase):
    def test_second_run_continues_numbering(self):
        seed("--count", "3", FLAG)
        seed("--count", "2", FLAG)

        emails = sorted(demo_users().values_list("email", flat=True))
        self.assertEqual(
            emails, [f"demo-{n}@example.invalid" for n in range(1, 6)]
        )

    def test_delete_removes_only_demo_users(self):
        real = make_account(email="real@example.com", username="real_person")
        lookalike = make_account(email="demo-x@example.invalid", username="lookalike")
        seed("--count", "5", FLAG)

        output = seed("--delete", FLAG)

        self.assertEqual(demo_users().count(), 0)
        self.assertEqual(Profile.objects.count(), 2)  # остались только «настоящий» и «похожий»
        self.assertTrue(User.objects.filter(pk=real.pk).exists())
        self.assertTrue(User.objects.filter(pk=lookalike.pk).exists())
        self.assertTrue(Profile.objects.filter(user=real).exists())
        self.assertIn("Удалено", output)

    def test_delete_with_nothing_to_delete_is_fine(self):
        seed("--delete", FLAG)

        self.assertEqual(User.objects.count(), 0)
