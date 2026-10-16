"""Правила блокировки — ЕДИНСТВЕННОЕ место, где решается «есть ли блокировка».

Блокировка действует в обе стороны (A заблокировал B ⇒ друг друга не видно в поиске, избранном,
профилях и новые запросы на переписку невозможны), но заблокированный о ней не узнаёт: везде, где он
мог бы заметить разницу, ответ неотличим от «человека нет» (404) или нейтральный (403 conversation_closed).
Все выборки — подзапросы Exists: число SQL-запросов не зависит от числа блокировок."""

from django.db.models import Exists, OuterRef, Q

from .models import Block


def are_blocked(user_id, other_id):
    """Есть ли блокировка между двумя людьми (в любую сторону)."""
    return Block.objects.filter(
        Q(blocker_id=user_id, blocked_id=other_id) | Q(blocker_id=other_id, blocked_id=user_id)
    ).exists()


def exclude_blocked(queryset, user, user_field):
    """Убирает из выборки людей, связанных с user блокировкой в любую сторону.
    user_field — поле выборки с id человека (например, "user_id")."""
    either_way = Block.objects.filter(
        Q(blocker=user, blocked_id=OuterRef(user_field))
        | Q(blocker_id=OuterRef(user_field), blocked=user)
    )
    return queryset.filter(~Exists(either_way))


def hidden_by_me(user):
    """Для выборки Conversation: диалог с человеком, которого заблокировал user (он у user скрыт).
    Заблокированный в паре — всегда partner, т.к. blocker=user сам один из участников."""
    mine = Block.objects.filter(blocker=user).filter(
        Q(blocked_id=OuterRef("user_a_id")) | Q(blocked_id=OuterRef("user_b_id"))
    )
    return Exists(mine)


def blocked_pair():
    """Для выборки Conversation: между участниками есть блокировка в любую сторону."""
    either_way = Block.objects.filter(
        Q(blocker_id=OuterRef("user_a_id"), blocked_id=OuterRef("user_b_id"))
        | Q(blocker_id=OuterRef("user_b_id"), blocked_id=OuterRef("user_a_id"))
    )
    return Exists(either_way)
