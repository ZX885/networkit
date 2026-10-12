"""python manage.py verify_user <email> — подтверждает почту тестового пользователя без письма
(для демо на Railway: запуск из консоли сервиса)."""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.users.models import User


class Command(BaseCommand):
    help = "Ставит email_verified_at пользователю (подтверждение почты без письма)."

    def add_arguments(self, parser):
        parser.add_argument("email", help="Email пользователя")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        user = User.objects.filter(email=email).first()
        if user is None:
            raise CommandError(f"Пользователь с email {email} не найден.")
        if user.email_verified_at:
            self.stdout.write(f"Почта {email} уже подтверждена.")
            return
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified_at"])
        self.stdout.write(self.style.SUCCESS(f"Почта {email} подтверждена."))
