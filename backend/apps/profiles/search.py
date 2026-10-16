"""Поиск людей: GET /api/profiles/. Правила приватности поиска — docs/SPEC.md §6.3:
- вуз участвует в поиске только у профилей с show_university=True;
- страна и город/регион — только у профилей с show_location=True;
- направление, статус, цели и языки публичны и фильтруются всегда.
"""

from django.db.models import Q
from django.db.models.functions import Lower, Trim
from rest_framework.exceptions import ErrorDetail, ValidationError

from apps.moderation.rules import exclude_blocked

from . import choices
from .models import Profile

Q_MAX_LENGTH = 100
MAX_TOKENS = 8  # слов в запросе: остальные игнорируются (защита от тяжёлых запросов)

# Параметр фильтра → допустимые коды
FILTER_CHOICES = {
    "country": choices.COUNTRIES,
    "city": choices.UZ_CITIES,
    "field": choices.FIELDS,
    "status": choices.STATUSES,
    "goal": choices.GOALS,
    "language": choices.LANGUAGES,
}


def visible_profiles():
    """Профили, которые можно показывать другим: аккаунт активен, не забанен, почта подтверждена."""
    return Profile.objects.select_related("user").filter(
        user__is_active=True,
        user__is_banned=False,
        user__email_verified_at__isnull=False,
    )


def clean_params(params):
    """Проверяет параметры запроса. Неизвестный код фильтра или слишком длинный q → 400."""
    errors = {}
    # NUL-символ PostgreSQL не принимает в тексте (был бы 500), в поиске он не нужен — убираем
    q = (params.get("q") or "").replace("\x00", "").strip()
    if len(q) > Q_MAX_LENGTH:
        errors["q"] = [ErrorDetail(f"Use at most {Q_MAX_LENGTH} characters.", code="too_long")]
    cleaned = {"q": q}
    for name, options in FILTER_CHOICES.items():
        value = (params.get(name) or "").strip()
        if value and value not in choices.codes(options):
            errors[name] = [ErrorDetail(f'"{value}" is not a valid choice.', code="invalid_choice")]
        cleaned[name] = value
    if errors:
        raise ValidationError(errors)
    return cleaned


def field_codes_matching(token):
    """Коды направлений, в названии которых есть слово (частичное, без учёта регистра)."""
    token = token.lower()
    return [code for code, label in choices.FIELDS if token in label.lower()]


def token_query(token):
    """Одно слово запроса: имя, фамилия, username, направление (по названию из справочника);
    вуз — только если он открыт; город и регион — только если открыто местоположение.
    icontains сам экранирует % и _ — подстановочных символов в запросе нет."""
    query = (
        Q(first_name__icontains=token)
        | Q(last_name__icontains=token)
        | Q(username__icontains=token)
        | Q(field__in=field_codes_matching(token))
    )
    query |= Q(show_university=True, university__icontains=token)
    query |= Q(show_location=True) & (Q(city__icontains=token) | Q(region__icontains=token))
    return query


def search_profiles(user, params):
    """Профили для поиска: без самого пользователя, без скрытых из поиска; новые первыми."""
    cleaned = clean_params(params)
    queryset = visible_profiles().filter(show_in_search=True).exclude(user=user)
    queryset = exclude_blocked(queryset, user, "user_id")  # блокировка в любую сторону

    for token in cleaned["q"].split()[:MAX_TOKENS]:
        queryset = queryset.filter(token_query(token))
    if cleaned["country"]:
        queryset = queryset.filter(show_location=True, country=cleaned["country"])
    if cleaned["city"]:
        # Город сравнивается с НАЗВАНИЕМ из справочника без учёта регистра и без пробелов по краям
        # (Lower(Trim(city))) и только среди show_location=True. Профили, у которых город «Other»
        # (любой город вне справочника), этим фильтром НЕ находятся — только текстовым поиском q.
        label = choices.label_of(choices.UZ_CITIES, cleaned["city"]).lower()
        queryset = queryset.annotate(city_normalized=Lower(Trim("city"))).filter(
            show_location=True, city_normalized=label
        )
    if cleaned["field"]:
        queryset = queryset.filter(field=cleaned["field"])
    if cleaned["status"]:
        queryset = queryset.filter(status=cleaned["status"])
    if cleaned["goal"]:
        queryset = queryset.filter(goals__contains=[cleaned["goal"]])
    if cleaned["language"]:
        queryset = queryset.filter(languages__contains=[cleaned["language"]])
    return queryset.order_by("-created_at", "-id")

