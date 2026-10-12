from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.users.models import User


class UserEmailTests(TestCase):
    def test_email_is_unique_ignoring_case_in_database(self):
        User.objects.create_user(email="user@example.com", password="pass-12345")

        # Обходим save(), который понижает регистр, — проверяем именно констрейнт БД
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(email="USER@example.com")])

    def test_email_is_unique_ignoring_case_in_validation(self):
        User.objects.create_user(email="user@example.com", password="pass-12345")

        with self.assertRaises(ValidationError):
            User(email="USER@Example.com").validate_constraints()

    def test_create_user_normalizes_email_to_lowercase(self):
        user = User.objects.create_user(email="  Jane.Doe@Example.COM ", password="pass-12345")

        self.assertEqual(user.email, "jane.doe@example.com")

    def test_second_user_with_other_case_is_rejected(self):
        User.objects.create_user(email="user@example.com", password="pass-12345")

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(email="USER@EXAMPLE.COM", password="pass-12345")

    def test_get_by_natural_key_ignores_case(self):
        user = User.objects.create_user(email="user@example.com", password="pass-12345")

        self.assertEqual(User.objects.get_by_natural_key("User@Example.com"), user)


class UserManagerTests(TestCase):
    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="pass-12345")

    def test_create_superuser_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email="", password="pass-12345")

    def test_create_superuser_sets_staff_and_superuser(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="pass-12345")

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_create_superuser_rejects_is_staff_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email="a@example.com", password="x", is_staff=False)

    def test_regular_user_has_no_admin_rights_and_is_not_banned(self):
        user = User.objects.create_user(email="user@example.com", password="pass-12345")

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_banned)
        self.assertIsNone(user.email_verified_at)

    def test_password_is_stored_as_hash(self):
        user = User.objects.create_user(email="user@example.com", password="pass-12345")

        self.assertNotEqual(user.password, "pass-12345")
        self.assertTrue(user.check_password("pass-12345"))
