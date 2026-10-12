"""Настройки боевого сервера (по умолчанию для wsgi/asgi). Строже, чем dev: ничего не угадываем."""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import env, require

DEBUG = env.bool("DEBUG", default=False)
if DEBUG:
    raise ImproperlyConfigured("В боевом режиме DEBUG должен быть False. Уберите DEBUG=True из окружения.")

# Список доменов обязателен, значения по умолчанию нет
ALLOWED_HOSTS = require("ALLOWED_HOSTS", env.list)
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS пуст. Укажите домены через запятую, например: networkit.example.com")

# Адрес сайта тоже обязателен (по нему строятся ссылки в письмах)
SITE_URL = require("SITE_URL")
