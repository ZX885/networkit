"""Блокировки и жалобы: правила и записи в базу. Текст жалобы нигде не логируется
(см. config/exceptions.py: ошибки по /api/reports/ и /api/blocks/ идут в лог без текста)."""

import uuid

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework.exceptions import ErrorDetail, NotFound, ValidationError

from apps.messaging.models import Conversation
from apps.profiles.models import Profile
from apps.profiles.search import visible_profiles
from apps.users.models import User
from config.exceptions import BlocksLimitReached, CannotTargetSelf

from .choices import REPORT_REASONS
from .models import Block, Report


def block_user(blocker, username):
    """PUT /blocks/{username}/: идемпотентно. Блокировать можно и того, кто заблокировал вас
    (ответ тот же: о чужой блокировке не сообщается)."""
    username = username.lower()
    own = Profile.objects.filter(user=blocker).values_list("username", flat=True).first()
    if username == own:
        raise CannotTargetSelf()
    target = visible_profiles().filter(username=username).first()
    if target is None:
        raise NotFound()  # нет такого, забанен, неактивен или не подтвердил почту
    with transaction.atomic():
        # Блокировка строки: параллельные запросы одного человека не обойдут лимит
        User.objects.select_for_update(no_key=True).filter(pk=blocker.pk).first()
        if Block.objects.filter(blocker=blocker, blocked=target.user).exists():
            return False
        if Block.objects.filter(blocker=blocker).count() >= settings.BLOCKS_MAX:
            raise BlocksLimitReached()
        Block.objects.create(blocker=blocker, blocked=target.user)
    return True


def unblock_user(blocker, username):
    """DELETE /blocks/{username}/: всегда 204 (разблокировать можно и недоступного человека)."""
    Block.objects.filter(blocker=blocker, blocked__profile__username=username.lower()).delete()


def _clean_reason(value):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError({"reason": [ErrorDetail("This field is required.", code="required")]})
    value = value.strip()
    if value not in [code for code, _label in REPORT_REASONS]:
        raise ValidationError(
            {"reason": [ErrorDetail(f'"{value}" is not a valid choice.', code="invalid_choice")]}
        )
    return value


def _clean_details(value):
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValidationError({"details": [ErrorDetail("Not a valid string.", code="invalid")]})
    text = value.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "").strip()
    if len(text) > settings.REPORT_DETAILS_MAX:
        raise ValidationError(
            {
                "details": [
                    ErrorDetail(
                        f"Use at most {settings.REPORT_DETAILS_MAX} characters.", code="too_long"
                    )
                ]
            }
        )
    return text


def _find_conversation(reporter, target, conversation_id):
    """Диалог для жалобы: reporter и target — его участники, иначе 404 (чужой диалог неотличим от
    несуществующего). Диалог, скрытый блокировкой, подходит: пожаловаться можно и после блокировки."""
    try:
        pk = uuid.UUID(str(conversation_id))
    except ValueError:
        raise NotFound() from None
    conversation = Conversation.objects.filter(pk=pk).filter(
        Q(user_a=reporter, user_b=target) | Q(user_a=target, user_b=reporter)
    ).first()
    if conversation is None:
        raise NotFound()
    return conversation


def create_report(reporter, data):
    """POST /reports/: всегда успех, если данные верны. Дубль открытой жалобы на того же человека
    ничего не создаёт и ничем не отличается в ответе (чтобы не раскрывать состояние)."""
    username = str(data.get("username") or "").strip().lower()
    reason = _clean_reason(data.get("reason"))
    details = _clean_details(data.get("details"))
    profile = Profile.objects.select_related("user").filter(
        username=username, user__is_active=True
    ).first()
    if profile is None:
        raise NotFound()
    target = profile.user
    if target.pk == reporter.pk:
        raise CannotTargetSelf()
    conversation = None
    if data.get("conversation_id") not in (None, ""):
        conversation = _find_conversation(reporter, target, data["conversation_id"])

    with transaction.atomic():
        existing = (
            Report.objects.select_for_update()
            .filter(reporter=reporter, target=target, status=Report.Status.OPEN)
            .first()
        )
        if existing is not None:
            if conversation is not None and existing.conversation_id is None:
                existing.conversation = conversation  # новая жалоба дополняет старую ссылкой на диалог
                existing.save(update_fields=["conversation"])
            return existing
        try:
            with transaction.atomic():  # savepoint: гонка двух одинаковых жалоб
                return Report.objects.create(
                    reporter=reporter,
                    target=target,
                    conversation=conversation,
                    reason=reason,
                    details=details,
                )
        except IntegrityError:
            return Report.objects.get(reporter=reporter, target=target, status=Report.Status.OPEN)
