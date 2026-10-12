from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "apps.users"  # путь импорта; label остаётся "users"
    default_auto_field = "django.db.models.BigAutoField"
