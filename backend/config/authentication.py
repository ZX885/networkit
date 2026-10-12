from rest_framework import exceptions
from rest_framework.authentication import SessionAuthentication

from .exceptions import CsrfFailed

SAFE_METHODS = ("GET", "HEAD", "OPTIONS", "TRACE")


class SessionAuth(SessionAuthentication):
    """Сессии Django с двумя отличиями от стандартного класса DRF."""

    def authenticate_header(self, request):
        # Наличие заголовка превращает ответ «не вошёл» из 403 в 401
        return "Session"

    def enforce_csrf(self, request):
        try:
            super().enforce_csrf(request)
        except exceptions.PermissionDenied:
            raise CsrfFailed() from None

    def authenticate(self, request):
        result = super().authenticate(request)
        # Стандартный DRF проверяет CSRF только у вошедших. Нам нужно и для анонимных запросов
        # (вход, регистрация): иначе чужой сайт мог бы «залогинить» посетителя в свой аккаунт.
        if result is None and request.method not in SAFE_METHODS:
            self.enforce_csrf(request)
        return result
