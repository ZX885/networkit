"""
Общие настройки NetworkIt. Значения, которые различаются между машинами и окружениями
(секретный ключ, база данных, адрес сайта), берутся из переменных окружения / файла backend/.env.
Режимы: dev.py (разработка) и prod.py (боевой сервер) импортируют всё отсюда.
"""

import os
import sys
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

# backend/ — папка с manage.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
ENV_FILE = BASE_DIR / ".env"
# SKIP_DOTENV=1 — не читать backend/.env (проверки боевых настроек: все значения только из окружения)
if ENV_FILE.exists() and os.environ.get("SKIP_DOTENV") != "1":
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


# Идёт ли сейчас `manage.py test` (тогда кэш — в памяти, лимиты запросов выключены)
TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

SECRET_KEY = require("SECRET_KEY")

# Адрес сайта (фронтенда): понадобится для ссылок в письмах
# Без завершающего слэша: из него строятся ссылки ({SITE_URL}/verify-email/…) и список доверенных origin
SITE_URL = env.str("SITE_URL", default="http://localhost:5173").rstrip("/")

# Сессия: cookie недоступна JS, живёт 14 дней и не продлевается (срок считается от входа)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_SAVE_EVERY_REQUEST = False

# CSRF: cookie читает JS (и отправляет в заголовке X-CSRFToken). Origin из списка считается своим:
# в dev запросы приходят через Vite-прокси с Origin http://localhost:5173
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
# По умолчанию — SITE_URL. Origin сравнивается строкой, поэтому слэш в конце убираем.
CSRF_TRUSTED_ORIGINS = [
    origin.strip().rstrip("/") for origin in env.list("CSRF_TRUSTED_ORIGINS", default=[SITE_URL])
]

# Письма: отправитель (backend почты задаётся в dev.py / prod.py)
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="NetworkIt <noreply@localhost>")

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
    "apps.messaging",
]

# Своя модель пользователя (вход по email). Должна быть задана до первой миграции.
AUTH_USER_MODEL = "users.User"

# Возраст: регистрация с MIN_AGE лет, младше ADULT_AGE — несовершеннолетний (контакты запрещены),
# старше MAX_AGE — вероятная опечатка в дате рождения. Те же числа во frontend/src/constants/rules.js.
MIN_AGE = 13
ADULT_AGE = 18
MAX_AGE = 100

# Сколько профилей человек может сохранить в избранное (отдаётся клиенту в /api/meta/ limits.saved_max)
SAVED_MAX = 200

# Личные сообщения: длина текста, число одновременно висящих исходящих запросов
# (pending и недавно отклонённые: отказ инициатору не раскрывается), срок «недавно» в днях
MESSAGE_MAX = 4000
REQUEST_MAX = 500  # первое сообщение вместе с запросом на переписку
PENDING_REQUESTS_MAX = 20
DECLINED_COUNTS_DAYS = 7

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
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    # Слабый пароль (Weak) отклоняется, нужен минимум Medium: apps/users/password_strength.py
    {"NAME": "apps.users.password_validators.PasswordStrengthValidator"},
]

# В тестах используем быстрый (небезопасный) хэш: настоящий PBKDF2 делает тесты в разы медленнее
if TESTING:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # сюда collectstatic собирает файлы админки (папка в .gitignore)

# Адрес админки (без слэша в начале, со слэшем в конце). На боевом сайте его можно сменить
ADMIN_URL = env.str("ADMIN_URL", default="admin/").strip().lstrip("/")
if not ADMIN_URL.endswith("/"):
    ADMIN_URL += "/"

# Демо без SMTP: ссылки подтверждения пишутся в лог одной строкой «DEMO link: …».
# Только для демо с тестовыми данными: на боевом сайте включать нельзя (ссылка = вход в чужой аккаунт).
DEMO_LOG_VERIFY_LINKS = env.bool("DEMO_LOG_VERIFY_LINKS", default=False)

# Логи приложения users (DEMO link) и ошибки сервера идут в консоль: на Railway это stdout контейнера
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "apps.users": {"handlers": ["console"], "level": "INFO"},
        # Трейсбеки ошибок попадают в stdout (на Railway это логи сервиса)
        "config.exceptions": {"handlers": ["console"], "level": "ERROR"},
        "django.request": {"handlers": ["console"], "level": "ERROR"},
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Кэш нужен для счётчиков лимитов запросов. На сервере — таблица в БД (общая для всех процессов
# Gunicorn); создаётся командой `python manage.py createcachetable`. В тестах — память процесса.
if TESTING:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "django_cache",
        }
    }

# Лимиты запросов (в минуту / в час). Подробности: docs/SPEC.md §3.0
THROTTLE_RATES = {
    "anon": "60/min",  # все анонимные запросы с одного IP
    "user": "300/min",  # все запросы вошедшего пользователя
    "login": "5/min",  # попытки входа с одного IP
    "login_hour": "30/hour",
    "register": "5/hour",  # регистрация и повторная отправка письма
    "username_check": "30/min",
    "search": "60/min",  # GET /api/profiles/ на пользователя
    "saved": "60/min",  # PUT/DELETE /api/saved/{username}/ на пользователя
    "message_request": "10/day",  # новые запросы на переписку
    "message_send": "30/min",  # сообщения в диалогах
    "message_send_day": "500/day",
    "email_flow": "5/hour",  # письма (сброс пароля, смена email): по IP
    "email_flow_day": "5/day",  # те же письма: по адресу email
    "account_password": "10/hour",  # проверки пароля (смена пароля, смена email, удаление): на пользователя
    "token_confirm": "30/hour",  # подтверждение по ссылке (сброс пароля, смена email): по IP
}
# Выключатель лимитов (в тестах выключены, отдельные тесты включают)
THROTTLING_ENABLED = env.bool("THROTTLING_ENABLED", default=not TESTING)

# Сколько прокси стоит перед Django (0 — клиент подключается напрямую). От этого зависит, какой
# IP считается адресом клиента: при неверном значении лимиты можно обойти заголовком X-Forwarded-For.
NUM_PROXIES = env.int("NUM_PROXIES", default=0)

# Django REST Framework: сессии Django + CSRF, по умолчанию нужен вход и аккаунт не забанен.
# Публичные view помечаются явно (permission_classes = [AllowAny]).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["config.authentication.SessionAuth"],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "config.permissions.IsNotBanned",
    ],
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardPagination",
    "DEFAULT_THROTTLE_CLASSES": ["config.throttles.AnonThrottle", "config.throttles.UserThrottle"],
    "DEFAULT_THROTTLE_RATES": THROTTLE_RATES,
    "EXCEPTION_HANDLER": "config.exceptions.exception_handler",
    "NUM_PROXIES": NUM_PROXIES,
}
