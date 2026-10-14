"""Настройки боевого сервера (по умолчанию для wsgi/asgi). Строже, чем dev: ничего не угадываем.
Всё берётся из переменных окружения; значения на Railway — в docs/DEPLOY.md."""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import (
    DEMO_LOG_VERIFY_LINKS,
    MIDDLEWARE,
    REST_FRAMEWORK,
    SITE_URL,
    env,
    require,
)

DEBUG = env.bool("DEBUG", default=False)
if DEBUG:
    raise ImproperlyConfigured("В боевом режиме DEBUG должен быть False. Уберите DEBUG=True из окружения.")

# Список доменов обязателен, значения по умолчанию нет.
# На Railway сюда нужно добавить и healthcheck.railway.app — иначе проверка здоровья получит 400.
ALLOWED_HOSTS = require("ALLOWED_HOSTS", env.list)
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS пуст. Укажите домены через запятую, например: networkit.example.com")

# Адрес сайта (его Vercel-домен) обязателен: по нему строятся ссылки в письмах и CSRF_TRUSTED_ORIGINS.
# CSRF_TRUSTED_ORIGINS и SITE_URL уже без завершающего слэша (см. base.py).
require("SITE_URL")
if not SITE_URL.startswith("https://"):
    raise ImproperlyConfigured("SITE_URL на боевом сайте должен начинаться с https://")

# Cookie сессии и CSRF только по HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# За прокси (Railway) HTTPS определяется по заголовку X-Forwarded-Proto.
# SECURE_SSL_REDIRECT намеренно НЕ включаем: он ломает проверки здоровья за прокси.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS — только если задана переменная (0 = выключено). Включайте после проверки, что HTTPS работает.
SECURE_HSTS_SECONDS = env.int("HSTS_SECONDS", default=0)

# Перед Django стоят Vercel и Railway: настоящий IP клиента — вторая запись с конца в X-Forwarded-For.
# Как проверить значение вручную — docs/DEPLOY.md.
NUM_PROXIES = env.int("NUM_PROXIES", default=2)
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "NUM_PROXIES": NUM_PROXIES,
    # Только JSON: браузерный интерфейс DRF (формы, HTML) на боевом сайте не нужен
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# Статика админки отдаётся самим приложением через WhiteNoise (сжатие + хэши в именах файлов)
MIDDLEWARE = [
    MIDDLEWARE[0],  # SecurityMiddleware должен идти первым
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Почта. Обычный режим — SMTP провайдера писем.
# Демо без SMTP (DEMO_LOG_VERIFY_LINKS=True и пустой EMAIL_HOST): письма печатаются в лог сервера.
EMAIL_HOST = env.str("EMAIL_HOST", default="")
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
elif DEMO_LOG_VERIFY_LINKS:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    raise ImproperlyConfigured(
        "EMAIL_HOST пуст. Укажите SMTP-сервер провайдера писем или, только для демо с тестовыми данными, "
        "включите DEMO_LOG_VERIFY_LINKS=True (ссылки будут в логе сервера)."
    )
