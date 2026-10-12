"""Корневые маршруты проекта."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from .views import health

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),  # ADMIN_URL из окружения, по умолчанию admin/
    path("api/health/", health, name="health"),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.profiles.urls")),
]

# JSON вместо HTML-страниц Django для адресов /api/
handler404 = "config.exceptions.not_found_view"
handler500 = "config.exceptions.server_error_view"
