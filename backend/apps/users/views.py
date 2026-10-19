from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError as DjangoValidationError
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.profiles.models import Profile
from apps.profiles.serializers import OwnProfileSerializer
from apps.profiles.validators import validate_username
from config.exceptions import (
    AccountBanned,
    AlreadyAuthenticated,
    EmailNotVerified,
    InvalidCredentials,
)
from config.throttles import (
    BASE_THROTTLES,
    AccountPasswordThrottle,
    EmailFlowDayThrottle,
    EmailFlowThrottle,
    LoginHourThrottle,
    LoginThrottle,
    RegisterThrottle,
    TokenConfirmThrottle,
    UsernameCheckThrottle,
)

from . import services
from .serializers import (
    EmailChangeSerializer,
    EmailSerializer,
    LoginSerializer,
    NewPasswordSerializer,
    PasswordChangeSerializer,
    RegisterSerializer,
)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def csrf(request):
    """GET /api/auth/csrf/ — ставит cookie csrftoken (фронтенд вызывает при старте)."""
    get_token(request._request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([*BASE_THROTTLES, UsernameCheckThrottle])
def username_available(request):
    """GET /api/auth/username-available/?username= — свободно ли имя (для подсказки при вводе)."""
    username = request.query_params.get("username", "").strip().lower()
    try:
        validate_username(username)
    except DjangoValidationError as exc:
        return Response({"available": False, "reason": exc.code})
    if Profile.objects.filter(username=username).exists():
        return Response({"available": False, "reason": "taken"})
    return Response({"available": True})


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [*BASE_THROTTLES, RegisterThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.register_account(serializer.validated_data)
        # Ответ всегда одинаковый, даже если email уже занят (не раскрываем, есть ли аккаунт)
        body = {"status": "verification_sent", "email": serializer.validated_data["email"]}
        return Response(body, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Любой странный ввод (пусто, не строка, не JSON-объект) — тот же invalid_token, а не 400 про поля
        data = request.data if isinstance(request.data, dict) else {}
        token = data.get("token")
        services.verify_email(token.strip() if isinstance(token, str) else "")
        return Response({"status": "verified"})  # сессию не создаём: дальше человек входит сам


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [*BASE_THROTTLES, RegisterThrottle]

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.resend_verification(serializer.validated_data["email"])
        return Response({"status": "sent"}, status=status.HTTP_202_ACCEPTED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [*BASE_THROTTLES, LoginThrottle, LoginHourThrottle]

    def post(self, request):
        if request.user.is_authenticated:
            raise AlreadyAuthenticated()
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request._request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        # Одна и та же ошибка для неверного пароля и неизвестного email
        if user is None:
            raise InvalidCredentials()
        # Про бан и неподтверждённую почту говорим только тому, кто знает верный пароль
        if user.is_banned:
            raise AccountBanned()
        if user.email_verified_at is None:
            raise EmailNotVerified()
        profile = Profile.objects.select_related("user").filter(user=user).first()
        if profile is None:
            raise PermissionDenied("This account cannot sign in here.")

        login(request._request, user)  # создаёт сессию, меняет её ключ и CSRF-токен
        return Response(OwnProfileSerializer(profile).data)


class LogoutView(APIView):
    def post(self, request):
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


def _body(request):
    """Тело запроса как словарь (всё остальное — пустой словарь: дальше обычная ошибка токена или поля)."""
    return request.data if isinstance(request.data, dict) else {}


class PasswordResetRequestView(APIView):
    """POST /api/auth/password-reset/ — всегда 202, есть ли такой аккаунт, не раскрывается."""

    permission_classes = [AllowAny]
    throttle_classes = [*BASE_THROTTLES, EmailFlowThrottle, EmailFlowDayThrottle]

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_password_reset(serializer.validated_data["email"])
        return Response({"status": "sent"}, status=status.HTTP_202_ACCEPTED)


class PasswordResetConfirmView(APIView):
    """POST /api/auth/password-reset/confirm/ — новый пароль по ссылке из письма (можно и вошедшему)."""

    permission_classes = [AllowAny]
    throttle_classes = [*BASE_THROTTLES, TokenConfirmThrottle]

    def post(self, request):
        data = _body(request)

        def get_new_password(user):
            serializer = NewPasswordSerializer(data=data, context={"user": user})
            serializer.is_valid(raise_exception=True)
            return serializer.validated_data["new_password"]

        services.reset_password(data.get("uid"), data.get("token"), get_new_password)
        return Response({"status": "password_changed"})


class PasswordChangeView(APIView):
    """POST /api/auth/password/change/ — смена пароля вошедшим (текущая сессия остаётся)."""

    throttle_classes = [*BASE_THROTTLES, AccountPasswordThrottle]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        services.change_password(
            request._request, request.user, serializer.validated_data["new_password"]
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmailChangeView(APIView):
    """POST /api/auth/email/change/ — письмо со ссылкой на новый адрес; ответ не зависит от того,
    занят ли адрес."""

    throttle_classes = [
        *BASE_THROTTLES,
        AccountPasswordThrottle,
        EmailFlowThrottle,
        EmailFlowDayThrottle,
    ]

    def post(self, request):
        serializer = EmailChangeSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        services.request_email_change(request.user, serializer.validated_data["new_email"])
        return Response({"status": "verification_sent"}, status=status.HTTP_202_ACCEPTED)


class EmailChangeConfirmView(APIView):
    """POST /api/auth/email/change/confirm/ — применяет смену адреса по ссылке (сессии остаются)."""

    permission_classes = [AllowAny]
    throttle_classes = [*BASE_THROTTLES, TokenConfirmThrottle]

    def post(self, request):
        token = _body(request).get("token")
        services.confirm_email_change(token.strip() if isinstance(token, str) else "")
        return Response({"status": "email_changed"})
