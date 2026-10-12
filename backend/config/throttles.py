"""Лимиты запросов. Числа лежат в settings.THROTTLE_RATES, включение — settings.THROTTLING_ENABLED."""

from django.conf import settings
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle


class SwitchableMixin:
    """Позволяет отключить лимит настройкой (нужно тестам)."""

    def allow_request(self, request, view):
        if not settings.THROTTLING_ENABLED:
            return True
        return super().allow_request(request, view)


class AnonThrottle(SwitchableMixin, AnonRateThrottle):
    scope = "anon"


class UserThrottle(SwitchableMixin, UserRateThrottle):
    scope = "user"


class IpThrottle(SwitchableMixin, SimpleRateThrottle):
    """Лимит по IP-адресу клиента (для входа, регистрации и т.п.)."""

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class LoginThrottle(IpThrottle):
    scope = "login"


class LoginHourThrottle(IpThrottle):
    scope = "login_hour"


class RegisterThrottle(IpThrottle):
    scope = "register"


class UsernameCheckThrottle(IpThrottle):
    scope = "username_check"


# Общие лимиты, которые нужно оставить у view, где throttle_classes задан явно
BASE_THROTTLES = [AnonThrottle, UserThrottle]
