"""Что показывается о человеке другим пользователям (docs/SPEC.md §6.1).

ВСЕ решения о показе полей собраны здесь: Card (поиск) и Public (страница профиля) только вызывают
эти методы. Нужно изменить правило (например, показывать несовершеннолетних сокращённым именем) —
меняется один метод, сериализаторы и тесты остаются прежними.
"""

from . import choices
from .models import CONTACT_FIELDS


class ProfileVisibility:
    """Публичное представление профиля с учётом приватности и возраста владельца."""

    def __init__(self, profile):
        self.profile = profile
        self.is_minor = profile.is_minor()  # младше ADULT_AGE (18)

    # ── Имя ──

    def name(self):
        """Отображаемое имя. Сейчас для всех (и несовершеннолетних) — полное имя.
        Единственное место, где это решение меняется (например, «Anna K.» для младше 18)."""
        return {"first_name": self.profile.first_name, "last_name": self.profile.last_name}

    # ── Поля, которые скрыты у несовершеннолетних независимо от настроек ──

    def school(self):
        """Школа — только у совершеннолетних. Отступление от SPEC §6.1 (там школа публична):
        школа несовершеннолетнего позволяет найти его в реальной жизни."""
        return None if self.is_minor else self.profile.school

    def contacts(self):
        """Контакты: только если владелец включил show_contacts И ему 18+; иначе null."""
        if self.is_minor or not self.profile.show_contacts:
            return None
        return {name: getattr(self.profile, name) for name in CONTACT_FIELDS}

    # ── Поля, которыми управляет сам человек ──

    def location(self):
        """Город, регион, страна — если show_location; иначе все null."""
        profile = self.profile
        if not profile.show_location:
            return {"city": None, "region": None, "country": None, "country_label": None}
        return {
            "city": profile.city,
            "region": profile.region,
            "country": profile.country,
            "country_label": choices.label_of(choices.COUNTRIES, profile.country),
        }

    def university(self):
        return self.profile.university if self.profile.show_university else None

    def joined(self):
        """Месяц и год регистрации («2026-09») — если show_join_date."""
        if not self.profile.show_join_date:
            return None
        return self.profile.created_at.strftime("%Y-%m")

    # ── Готовые представления ──

    def card(self):
        """Card (поиск, избранное): без школы, вуза, контактов и даты регистрации."""
        profile = self.profile
        location = self.location()
        return {
            "username": profile.username,
            **self.name(),
            "avatar_url": None,  # загрузка аватара появится в B4b
            "field": profile.field,
            "field_label": choices.label_of(choices.FIELDS, profile.field),
            "status": profile.status,
            "status_label": choices.label_of(choices.STATUSES, profile.status),
            "city": location["city"],
            "country": location["country"],
            "country_label": location["country_label"],
            "bio": profile.bio,
            "interests": profile.interests,
            "is_saved": False,  # избранное появится в B9
        }

    def public(self):
        """Public (страница профиля). Скрытое поле — null, а не пропуск."""
        profile = self.profile
        return {
            **self.card(),
            "region": self.location()["region"],
            "school": self.school(),
            "university": self.university(),
            "year_level": profile.year_level,
            "languages": profile.languages,
            "goals": profile.goals,
            "contacts": self.contacts(),
            "joined": self.joined(),
        }

