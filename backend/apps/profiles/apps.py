from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    name = "apps.profiles"  # путь импорта; label остаётся "profiles"
    default_auto_field = "django.db.models.BigAutoField"
