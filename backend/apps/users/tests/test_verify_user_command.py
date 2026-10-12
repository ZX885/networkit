from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.users.models import User

from .helpers import make_account


class VerifyUserCommandTests(TestCase):
    def run_command(self, email):
        out = StringIO()
        call_command("verify_user", email, stdout=out)
        return out.getvalue()

    def test_confirms_email_of_unverified_user(self):
        user = make_account(email="demo@example.com", verified=False)

        self.run_command("Demo@Example.com")  # регистр не важен

        user.refresh_from_db()
        self.assertIsNotNone(user.email_verified_at)

    def test_second_run_keeps_original_time(self):
        user = make_account(email="demo@example.com")
        before = User.objects.get(pk=user.pk).email_verified_at

        output = self.run_command("demo@example.com")

        self.assertIn("уже подтверждена", output)
        self.assertEqual(User.objects.get(pk=user.pk).email_verified_at, before)

    def test_unknown_email_is_an_error(self):
        with self.assertRaises(CommandError):
            self.run_command("nobody@example.com")
