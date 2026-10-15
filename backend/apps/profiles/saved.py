"""Избранное (закладки): правила и запросы. Видимость сохранённого человека — как в поиске
(search.visible_profiles); приватность полей карточки решает ProfileVisibility."""

from django.conf import settings
from django.db import transaction

from apps.users.models import User
from config.exceptions import SavedLimitReached

from .models import SavedProfile


def saved_user_ids(owner, user_ids):
    """Какие из user_ids сохранил owner: ОДИН запрос на страницу (без N+1)."""
    ids = list(user_ids)
    if not ids:
        return set()
    return set(
        SavedProfile.objects.filter(owner=owner, saved_user_id__in=ids).values_list(
            "saved_user_id", flat=True
        )
    )


def is_saved(owner, saved_user_id):
    return SavedProfile.objects.filter(owner=owner, saved_user_id=saved_user_id).exists()


def saved_list(owner):
    """Закладки владельца для списка: сохранённый человек виден всем (активен, не забанен,
    почта подтверждена, профиль есть). show_in_search=False закладку НЕ скрывает.
    Новые закладки первыми; профиль подтягивается одним запросом."""
    return (
        SavedProfile.objects.filter(
            owner=owner,
            saved_user__is_active=True,
            saved_user__is_banned=False,
            saved_user__email_verified_at__isnull=False,
            saved_user__profile__isnull=False,
        )
        .select_related("saved_user__profile")
        .order_by("-created_at", "-id")
    )


def add_saved(owner, target_user):
    """Добавляет закладку (повтор уже сохранённого — без изменений, лимит не проверяется).

    Проверка лимита и вставка идут в одной транзакции под блокировкой строки владельца:
    параллельные запросы одного человека выстраиваются в очередь и не могут вместе обойти лимит."""
    with transaction.atomic():
        User.objects.select_for_update().filter(pk=owner.pk).first()  # блокировка владельца
        if SavedProfile.objects.filter(owner=owner, saved_user=target_user).exists():
            return False
        # Считаем только видимые закладки (как в списке): скрытые из списка нельзя было бы убрать
        if saved_list(owner).count() >= settings.SAVED_MAX:
            raise SavedLimitReached()
        SavedProfile.objects.create(owner=owner, saved_user=target_user)
        return True
