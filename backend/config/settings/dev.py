"""Настройки для разработки (по умолчанию для manage.py)."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Письма печатаются в консоль, где запущен runserver (подтверждение почты — ссылка из письма)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
