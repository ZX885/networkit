from django.apps import AppConfig


class MessagingConfig(AppConfig):
    name = "apps.messaging"  # путь импорта; label остаётся "messaging"
    default_auto_field = "django.db.models.BigAutoField"
