"""Боевые настройки проверяем в отдельном процессе: так не мешают переменные окружения тестов
и файл backend/.env. Все важные переменные задаются явно."""

import json
import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

BACKEND_DIR = Path(__file__).resolve().parents[2]

GOOD_ENV = {
    "DJANGO_SETTINGS_MODULE": "config.settings.prod",
    "SKIP_DOTENV": "1",  # файл backend/.env не читаем
    "SECRET_KEY": "test-secret-key-not-used-anywhere",
    "DEBUG": "False",
    "DATABASE_URL": "postgresql://user:pass@postgres.railway.internal:5432/railway",
    "ALLOWED_HOSTS": "api.example.up.railway.app,healthcheck.railway.app",
    "SITE_URL": "https://site.example.vercel.app/",
    "EMAIL_HOST": "smtp.example.com",
    "DEMO_LOG_VERIFY_LINKS": "False",
}

PRINT_SETTINGS = """
import json
from django.conf import settings
print("JSON:" + json.dumps({
    "debug": settings.DEBUG,
    "engine": settings.DATABASES["default"]["ENGINE"],
    "site_url": settings.SITE_URL,
    "csrf": settings.CSRF_TRUSTED_ORIGINS,
    "proxy_header": settings.SECURE_PROXY_SSL_HEADER,
    "ssl_redirect": settings.SECURE_SSL_REDIRECT,
    "hsts": settings.SECURE_HSTS_SECONDS,
    "num_proxies": settings.NUM_PROXIES,
    "drf_proxies": settings.REST_FRAMEWORK["NUM_PROXIES"],
    "session_secure": settings.SESSION_COOKIE_SECURE,
    "csrf_secure": settings.CSRF_COOKIE_SECURE,
    "admin_url": settings.ADMIN_URL,
    "middleware": settings.MIDDLEWARE[:2],
    "email_backend": settings.EMAIL_BACKEND,
    "static_root": str(settings.STATIC_ROOT),
}))
"""


def load_prod(**overrides):
    """Запускает prod-настройки с заданным окружением. Возвращает (код, настройки, текст ошибки)."""
    optional = ("NUM_PROXIES", "HSTS_SECONDS", "ADMIN_URL", "CSRF_TRUSTED_ORIGINS")
    env = {k: v for k, v in os.environ.items() if k not in GOOD_ENV and k not in optional}
    env.update({**GOOD_ENV, **overrides})
    env = {k: v for k, v in env.items() if v is not None}  # None в overrides = переменной нет
    result = subprocess.run(
        [sys.executable, "-c", PRINT_SETTINGS], cwd=BACKEND_DIR, env=env, capture_output=True, text=True
    )
    line = next((x for x in result.stdout.splitlines() if x.startswith("JSON:")), None)
    return result.returncode, json.loads(line[5:]) if line else None, result.stderr


class ProdSettingsTests(SimpleTestCase):
    def test_good_environment(self):
        code, conf, err = load_prod(CSRF_TRUSTED_ORIGINS="https://site.example.vercel.app/")

        self.assertEqual(code, 0, err)
        self.assertFalse(conf["debug"])
        self.assertIn("postgresql", conf["engine"])  # postgresql:// с Railway принимается
        self.assertEqual(conf["site_url"], "https://site.example.vercel.app")  # без слэша
        self.assertEqual(conf["csrf"], ["https://site.example.vercel.app"])
        self.assertEqual(conf["proxy_header"], ["HTTP_X_FORWARDED_PROTO", "https"])
        self.assertFalse(conf["ssl_redirect"])
        self.assertEqual(conf["hsts"], 0)
        self.assertEqual((conf["num_proxies"], conf["drf_proxies"]), (2, 2))
        self.assertTrue(conf["session_secure"] and conf["csrf_secure"])
        self.assertEqual(conf["admin_url"], "admin/")
        self.assertEqual(conf["middleware"][1], "whitenoise.middleware.WhiteNoiseMiddleware")
        self.assertTrue(conf["static_root"].endswith("staticfiles"))

    def test_csrf_origins_default_to_site_url_without_trailing_slash(self):
        code, conf, err = load_prod(CSRF_TRUSTED_ORIGINS=None)

        self.assertEqual(code, 0, err)
        self.assertEqual(conf["csrf"], ["https://site.example.vercel.app"])

    def test_variables_are_read_from_environment(self):
        code, conf, err = load_prod(NUM_PROXIES="1", HSTS_SECONDS="3600", ADMIN_URL="/secret-panel")

        self.assertEqual(code, 0, err)
        self.assertEqual((conf["num_proxies"], conf["hsts"]), (1, 3600))
        self.assertEqual(conf["admin_url"], "secret-panel/")

    def test_debug_true_is_refused(self):
        code, _, err = load_prod(DEBUG="True")

        self.assertNotEqual(code, 0)
        self.assertIn("DEBUG", err)

    def test_http_site_url_is_refused(self):
        code, _, err = load_prod(SITE_URL="http://site.example.com")

        self.assertNotEqual(code, 0)
        self.assertIn("https://", err)

    def test_email_needs_smtp_or_demo_flag(self):
        code, _, err = load_prod(EMAIL_HOST="")
        self.assertNotEqual(code, 0)
        self.assertIn("EMAIL_HOST", err)

        code, conf, err = load_prod(EMAIL_HOST="", DEMO_LOG_VERIFY_LINKS="True")
        self.assertEqual(code, 0, err)
        self.assertTrue(conf["email_backend"].endswith("console.EmailBackend"))
