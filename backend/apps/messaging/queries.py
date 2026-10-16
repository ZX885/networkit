"""Выборки диалогов и сообщений. Список диалогов — без N+1: последнее сообщение и счётчик
непрочитанных считаются аннотациями (подзапросами), собеседник и его профиль — select_related."""

from django.db.models import Case, Count, F, IntegerField, OuterRef, Q, Subquery, Value, When
from django.db.models.functions import Coalesce

from apps.moderation.rules import blocked_pair, hidden_by_me

from .models import Conversation, Message

Status = Conversation.Status


def _partner_is_visible(user):
    """Собеседник активен, не забанен, почта подтверждена (иначе диалог скрыт: данные сохраняются)."""
    ok = {"is_active": True, "is_banned": False, "email_verified_at__isnull": False}
    return Q(user_a=user, **{f"user_b__{k}": v for k, v in ok.items()}) | Q(
        user_b=user, **{f"user_a__{k}": v for k, v in ok.items()}
    )


def participant_conversations(user):
    """Диалоги, в которых участвует user и собеседник которых виден. Диалоги с человеком, которого
    user заблокировал, скрыты; у заблокированного диалог остаётся (он не должен узнать о блокировке)."""
    return Conversation.objects.filter(_partner_is_visible(user)).filter(~hidden_by_me(user))


def annotated(user, queryset=None):
    """Добавляет к диалогам: последнее сообщение, счётчик непрочитанных, данные собеседника."""
    queryset = participant_conversations(user) if queryset is None else queryset
    last = Message.objects.filter(conversation=OuterRef("pk")).order_by("-id")
    unread = (
        Message.objects.filter(conversation=OuterRef("pk"), seen_at__isnull=True)
        .exclude(sender=user)
        .order_by()
        .values("conversation")
        .annotate(total=Count("id"))
        .values("total")
    )
    return queryset.select_related("user_a__profile", "user_b__profile").annotate(
        last_body=Subquery(last.values("body")[:1]),
        last_sender_id=Subquery(last.values("sender_id")[:1]),
        last_created_at=Subquery(last.values("created_at")[:1]),
        # Непрочитанные считаются только в принятых диалогах (запросы — отдельный счётчик)
        unread_count=Case(
            When(status=Status.ACCEPTED, then=Coalesce(Subquery(unread, output_field=IntegerField()), 0)),
            default=Value(0),
            output_field=IntegerField(),
        ),
    )


def box_conversations(user, box):
    """Диалоги для вкладки: chats — принятые; requests — входящие pending; sent — мои исходящие
    запросы (declined показывается как pending: отказ инициатору не раскрывается)."""
    queryset = participant_conversations(user)
    if box == "requests":
        queryset = queryset.filter(status=Status.PENDING).exclude(initiator=user)
    elif box == "sent":
        queryset = queryset.filter(initiator=user, status__in=[Status.PENDING, Status.DECLINED])
    else:
        queryset = queryset.filter(status=Status.ACCEPTED)
    return annotated(user, queryset).order_by(
        F("last_message_at").desc(nulls_last=True), "-created_at", "-id"
    )


def summary(user):
    """Счётчики для бейджей: непрочитанные входящие в принятых диалогах и входящие запросы."""
    visible = participant_conversations(user)
    unread = (
        Message.objects.filter(conversation__in=visible.filter(status=Status.ACCEPTED), seen_at__isnull=True)
        .exclude(sender=user)
        .count()
    )
    # Запросы от/к заблокированному (в любую сторону) в счётчик не попадают
    pending = (
        visible.filter(status=Status.PENDING)
        .exclude(initiator=user)
        .filter(~blocked_pair())
        .count()
    )
    return {"unread_messages": unread, "pending_requests": pending}
