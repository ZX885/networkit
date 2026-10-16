"""Действия с диалогами и сообщениями. Все проверки состояния и записи в базу — здесь.
Тело сообщения нигде не логируется (см. config/exceptions.py: ошибки по /api/conversations/ в логе
идут без текста)."""

from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ErrorDetail, NotFound, ValidationError

from apps.moderation.rules import are_blocked
from apps.profiles.search import visible_profiles
from apps.users.models import User
from config.exceptions import (
    AcceptRequired,
    CannotTargetSelf,
    ConversationClosed,
    ConversationExists,
    IncomingRequestExists,
    InvalidState,
    PendingRequestsLimit,
    RequestPending,
)

from .models import Conversation, Message
from .rules import SELF, can_start_conversation

Status = Conversation.Status


def clean_body(value, max_length):
    """Текст сообщения: \\r\\n → \\n, strip, 1..max_length символов. Без какой-либо HTML-обработки."""
    if not isinstance(value, str):
        raise ValidationError({"body": [ErrorDetail("Enter a message.", code="invalid")]})
    text = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        raise ValidationError({"body": [ErrorDetail("Enter a message.", code="required")]})
    if len(text) > max_length:
        raise ValidationError(
            {"body": [ErrorDetail(f"Use at most {max_length} characters.", code="too_long")]}
        )
    return text


def outgoing_requests_count(user):
    """Висящие исходящие запросы: pending всегда, declined — только DECLINED_COUNTS_DAYS дней после
    решения (иначе освободившийся слот выдал бы отказ: инициатор видит declined как pending)."""
    since = timezone.now() - timedelta(days=settings.DECLINED_COUNTS_DAYS)
    return Conversation.objects.filter(initiator=user).filter(
        Q(status=Status.PENDING) | Q(status=Status.DECLINED, decided_at__gt=since)
    ).count()


def _existing_conflict(conversation, sender):
    """Какая ошибка соответствует уже существующему диалогу (для POST /conversations/)."""
    extra = {"conversation_id": str(conversation.pk)}
    if conversation.status == Status.ACCEPTED:
        return ConversationExists(extra=extra)
    if conversation.initiator_id == sender.pk:
        return RequestPending(extra=extra)  # pending и declined выглядят одинаково (маскирование)
    if conversation.status == Status.PENDING:
        return IncomingRequestExists(extra=extra)
    return ConversationClosed()  # входящий запрос, который я сам отклонил


def create_request(sender, username, body):
    """POST /conversations/: запрос на переписку + первое сообщение в одной транзакции."""
    text = clean_body(body, settings.REQUEST_MAX)
    target_profile = visible_profiles().filter(username=str(username).lower()).first()
    if target_profile is None:
        raise NotFound()
    target = target_profile.user
    reason = can_start_conversation(sender, target)
    if reason == SELF:
        raise CannotTargetSelf()
    if reason is not None:
        raise NotFound()
    if are_blocked(sender.pk, target.pk):
        raise NotFound()  # блокировка в любую сторону: цель «не существует», причина не раскрывается

    user_a, user_b = sorted([sender, target], key=lambda user: user.pk)
    with transaction.atomic():
        # Блокировка строки отправителя: его запросы выстраиваются в очередь (лимит висящих не обойти).
        # no_key=True (FOR NO KEY UPDATE) обязательно: обычный FOR UPDATE конфликтует с проверкой
        # внешних ключей (KEY SHARE) при вставке диалога, и два встречных запроса зависали бы друг на
        # друге (deadlock)
        User.objects.select_for_update(no_key=True).filter(pk=sender.pk).first()
        existing = Conversation.objects.filter(user_a=user_a, user_b=user_b).first()
        if existing is not None:
            raise _existing_conflict(existing, sender)
        if outgoing_requests_count(sender) >= settings.PENDING_REQUESTS_MAX:
            raise PendingRequestsLimit()
        now = timezone.now()
        try:
            with transaction.atomic():  # savepoint: гонка встречных запросов даёт IntegrityError
                conversation = Conversation.objects.create(
                    user_a=user_a,
                    user_b=user_b,
                    initiator=sender,
                    status=Status.PENDING,
                    last_message_at=now,
                )
        except IntegrityError:
            existing = Conversation.objects.get(user_a=user_a, user_b=user_b)
            raise _existing_conflict(existing, sender) from None
        Message.objects.create(conversation=conversation, sender=sender, body=text)
    return conversation


def decide(conversation_id, user, accept):
    """accept/decline: только получатель и только из pending, иначе 409 invalid_state
    (инициатору — всегда invalid_state, чтобы отказ оставался замаскированным)."""
    with transaction.atomic():
        conversation = Conversation.objects.select_for_update().get(pk=conversation_id)
        if are_blocked(conversation.user_a_id, conversation.user_b_id):
            raise ConversationClosed()
        if conversation.recipient_id != user.pk or conversation.status != Status.PENDING:
            raise InvalidState()
        conversation.status = Status.ACCEPTED if accept else Status.DECLINED
        conversation.decided_at = timezone.now()
        conversation.save(update_fields=["status", "decided_at"])
    return conversation


def send_message(conversation_id, sender, body):
    """POST /conversations/{id}/messages/: правила отправки (docs/SPEC.md §7.3)."""
    text = clean_body(body, settings.MESSAGE_MAX)
    with transaction.atomic():
        conversation = Conversation.objects.select_for_update().get(pk=conversation_id)
        if not conversation.is_member(sender):
            raise NotFound()  # на случай прямого вызова: участники проверяются во view
        if are_blocked(conversation.user_a_id, conversation.user_b_id):
            raise ConversationClosed()  # нейтральный текст: о блокировке не сообщается
        is_initiator = conversation.initiator_id == sender.pk
        if conversation.status == Status.PENDING:
            raise RequestPending() if is_initiator else AcceptRequired()
        if conversation.status == Status.DECLINED:
            # Инициатор не должен узнать об отказе: для него это всё ещё «запрос ожидает»
            raise RequestPending() if is_initiator else ConversationClosed()
        message = Message.objects.create(conversation=conversation, sender=sender, body=text)
        conversation.last_message_at = message.created_at
        conversation.save(update_fields=["last_message_at"])
    return message


def mark_read(conversation, user):
    """Помечает входящие прочитанными — только в принятых диалогах (в pending/declined ничего:
    иначе инициатор по seen_at узнал бы, что получатель открыл запрос до решения). Возвращает число."""
    if conversation.status != Status.ACCEPTED:
        return 0
    return (
        Message.objects.filter(conversation=conversation, seen_at__isnull=True)
        .exclude(sender=user)
        .update(seen_at=timezone.now())
    )
