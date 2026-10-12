"""
Общие настройки NetworkIt. Значения, которые различаются между машинами и окружениями
(секретный ключ, база данных, адрес сайта), берутся из переменных окружения / файла backend/.env.
Режимы: dev.py (разработка) и prod.py (боевой сервер) импортируют всё отсюда.
"""

from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

# backend/ — папка с manage.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    environ.Env.read_env(ENV_FILE)


def require(name, getter=env.str):
    """Обязательная переменная окружения: если её нет — понятная ошибка вместо traceback."""
    try:
        return getter(name)
    except ImproperlyConfigured:
        hint = "Файл backend/.env не найден. " if not ENV_FILE.exists() else ""
        raise ImproperlyConfigured(
            f"{hint}Не задана переменная окружения {name}. "
            "Скопируйте backend/.env.example в backend/.env и заполните её (см. README.md)."
        ) from None


SECRET_KEY = require("SECRET_KEY")

# Адрес сайта (фронтенда): понадобится для ссылок в письмах
SITE_URL = env.str("SITE_URL", default="http://localhost:5173")

# База данных — только PostgreSQL, строка вида postgres://пользователь:пароль@127.0.0.1:5432/имя_базы
DATABASES = {"default": env.db_url_config(require("DATABASE_URL"))}
if "postgresql" not in DATABASES["default"]["ENGINE"]:
    raise ImproperlyConfigured(
        "DATABASE_URL должен указывать на PostgreSQL: postgres://пользователь:пароль@127.0.0.1:5432/база"
    )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",  # нужен для ArrayField и GinIndex (проверка postgres.E005)
    "rest_framework",
    "apps.users",
    "apps.profiles",
]

# Своя модель пользователя (вход по email). Должна быть задана до первой миграции.
AUTH_USER_MODEL = "users.User"

# Возраст: регистрация с MIN_AGE лет, младше ADULT_AGE — несовершеннолетний (контакты запрещены),
# старше MAX_AGE — вероятная опечатка в дате рождения. Те же числа во frontend/src/constants/rules.js.
MIN_AGE = 13
ADULT_AGE = 18
MAX_AGE = 100

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework: сессии Django + CSRF, по умолчанию нужен вход.
# Публичные view помечаются явно (permission_classes = [AllowAny]).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardPagination",
}
