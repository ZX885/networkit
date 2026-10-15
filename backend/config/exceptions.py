"""
Единый формат ошибок API (docs/SPEC.md §3.0):

    {"error": {"code": "...", "message": "...", "fields": {...}, "non_field_errors": [...]}}

`fields` и `non_field_errors` есть только у ошибок валидации (400 validation_error).
"""

import logging
from math import ceil

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404, JsonResponse
from django.views import defaults
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.settings import api_settings

logger = logging.getLogger(__name__)


# ── Свои ошибки: у каждой свой код, который фронтенд превращает в текст ──


class _ApiError(exceptions.APIException):
    """Базовый класс: status_code, default_code и default_detail задаются в наследнике.
    extra — дополнительные поля тела ошибки (например, conversation_id)."""

    def __init__(self, detail=None, code=None, extra=None):
        super().__init__(detail, code)
        self.extra = extra or {}


class InvalidCredentials(_ApiError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "invalid_credentials"
    default_detail = "Incorrect email or password."


class CannotTargetSelf(_ApiError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "cannot_target_self"
    default_detail = "You cannot do this with your own profile."


class SavedLimitReached(_ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "saved_limit_reached"
    default_detail = "You have reached the limit of saved profiles."


class ConversationExists(_ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conversation_exists"
    default_detail = "You already have a conversation with this person."


class RequestPending(_ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "request_pending"
    default_detail = "Your message request is waiting for a reply."


class IncomingRequestExists(_ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "incoming_request_exists"
    default_detail = "This person has already sent you a message request. Accept it to start chatting."


class InvalidState(_ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "invalid_state"
    default_detail = "This action is not available now."


class PendingRequestsLimit(_ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "pending_requests_limit_reached"
    default_detail = "You have too many message requests waiting for a reply."


class AcceptRequired(_ApiError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "accept_required"
    default_detail = "Accept the message request first."


class ConversationClosed(_ApiError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "conversation_closed"
    default_detail = "You can't send messages to this user."


class InvalidToken(_ApiError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "invalid_token"
    default_detail = "This link is invalid or has expired."


class EmailNotVerified(_ApiError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "email_not_verified"
    default_detail = "Please confirm your email address first."


class AccountBanned(_ApiError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "account_banned"
    default_detail = "This account has been suspended."


class AlreadyAuthenticated(_ApiError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "already_authenticated"
    default_detail = "You are already signed in."


class CsrfFailed(_ApiError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "csrf_failed"
    default_detail = "CSRF verification failed."


# ── Преобразование ошибок в единый формат ──

# Коды DRF/Django приводим к кодам из SPEC §5
CODE_ALIASES = {
    "blank": "required",
    "null": "required",
    "max_length": "too_long",
    "min_length": "too_short",
    "authentication_failed": "not_authenticated",
}


def normalize_code(code):
    code = str(code)
    if code.startswith("password_"):  # password_too_short → too_short
        code = code[len("password_") :]
    return CODE_ALIASES.get(code, code)


def _entry(error):
    return {"code": normalize_code(error.code), "message": str(error)}


def _collect(detail, path, fields, non_field):
    """Раскладывает detail ValidationError: ошибки полей (ключи вложенных — через точку) и общие."""
    if isinstance(detail, dict):
        for key, value in detail.items():
            if not path and key == api_settings.NON_FIELD_ERRORS_KEY:
                _collect(value, "", fields, non_field)
            else:
                _collect(value, f"{path}.{key}" if path else str(key), fields, non_field)
    elif isinstance(detail, list):
        for item in detail:
            _collect(item, path, fields, non_field)
    elif path:
        fields.setdefault(path, []).append(_entry(detail))
    else:
        non_field.append(_entry(detail))


# Сообщения людей нельзя выводить в логи: ошибки БД содержат строку целиком («Failing row contains …»),
# а у исключений из текста сообщения бывает текст в самом сообщении об ошибке.
PRIVATE_PATH_PREFIXES = ("/api/conversations/",)


class RedactedError(Exception):
    """Замена исходной ошибки в логе: тип и место в коде (трейсбек) остаются, текст ошибки скрыт."""


def _log_exc_info(exc, path):
    if not path.startswith(PRIVATE_PATH_PREFIXES):
        return exc
    safe = RedactedError(f"{type(exc).__module__}.{type(exc).__qualname__} (details hidden)")
    safe.__cause__ = None  # цепочка «caused by» тоже содержит исходный текст
    safe.__suppress_context__ = True
    return (RedactedError, safe, exc.__traceback__)


def error_body(code, message, **extra):
    return {"error": {"code": code, "message": message, **extra}}


def exception_handler(exc, context):
    """Обработчик исключений DRF. Неожиданные исключения (баги) пишем в лог с трейсбеком, а клиенту
    отдаём нейтральный server_error без деталей."""
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied()
    if not isinstance(exc, exceptions.APIException):
        request = context.get("request")
        logger.error(
            "Unhandled exception in API view: %s %s",
            getattr(request, "method", "?"),
            getattr(request, "path", "?"),
            exc_info=_log_exc_info(exc, getattr(request, "path", "")),
        )
        return Response(
            error_body("server_error", "Something went wrong."),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    headers = {}
    if isinstance(exc, exceptions.ValidationError):
        fields, non_field = {}, []
        _collect(exc.detail, "", fields, non_field)
        body = error_body(
            "validation_error",
            "Please correct the highlighted fields.",
            fields=fields,
            non_field_errors=non_field,
        )
        return Response(body, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, exceptions.ParseError):
        body = error_body(
            "validation_error",
            "Malformed request body.",
            fields={},
            non_field_errors=[{"code": "parse_error", "message": "Malformed request body."}],
        )
        return Response(body, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, exceptions.Throttled):
        wait = ceil(exc.wait) if exc.wait else 1
        headers["Retry-After"] = str(wait)
        body = error_body(
            "throttled", f"Too many requests. Try again in {wait} seconds.", retry_after=wait
        )
        return Response(body, status=status.HTTP_429_TOO_MANY_REQUESTS, headers=headers)

    if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
        if getattr(exc, "auth_header", None):
            headers["WWW-Authenticate"] = exc.auth_header
        body = error_body("not_authenticated", "Authentication is required.")
        return Response(body, status=status.HTTP_401_UNAUTHORIZED, headers=headers)

    # Остальные: код и текст берём из самого исключения (permission_denied, not_found, свои…)
    code = normalize_code(exc.get_codes() if isinstance(exc.get_codes(), str) else exc.default_code)
    extra = getattr(exc, "extra", {})
    return Response(error_body(code, str(exc.detail), **extra), status=exc.status_code)


# ── JSON-ответы для /api/ вместо HTML-страниц Django (404 и 500) ──


def not_found_view(request, exception=None):
    if request.path.startswith("/api/"):
        return JsonResponse(error_body("not_found", "Not found."), status=404)
    return defaults.page_not_found(request, exception)


def server_error_view(request):
    if request.path.startswith("/api/"):
        # Без деталей: причина ошибки пишется только в лог сервера
        return JsonResponse(error_body("server_error", "Something went wrong."), status=500)
    return defaults.server_error(request)
