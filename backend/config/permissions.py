from rest_framework.permissions import BasePermission

from .exceptions import AccountBanned


class IsNotBanned(BasePermission):
    """Забаненный пользователь не может пользоваться API (403 account_banned).

    Подключён глобально после IsAuthenticated. Публичные view (AllowAny) её не используют.
    """

    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated and user.is_banned:
            raise AccountBanned()
        return True
