"""Правила начала диалога. Все решения «можно ли написать этому человеку» собраны здесь,
чтобы позже добавить правило (например, про возраст) в одном месте."""

SELF = "self"
UNAVAILABLE = "unavailable"


def can_start_conversation(sender, target):
    """Можно ли sender начать диалог с target (оба — User).

    Возвращает None, если можно, иначе причину: SELF (свой профиль) или UNAVAILABLE (цель недоступна:
    нет аккаунта-профиля, забанена, неактивна или не подтвердила почту). show_in_search=False
    диалогу не мешает. Ограничений по возрасту сейчас нет: их добавлять здесь."""
    if sender.pk == target.pk:
        return SELF
    profile = getattr(target, "profile", None)
    if (
        profile is None
        or not target.is_active
        or target.is_banned
        or target.email_verified_at is None
    ):
        return UNAVAILABLE
    return None
