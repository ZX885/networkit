"""Сериализаторы профиля: общие поля (регистрация и PATCH /api/me/) и ответ Own."""

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from . import choices
from .age import calculate_age
from .models import (
    CONTACT_FIELDS,
    GOALS_MAX,
    INTERESTS_MAX,
    LANGUAGES_MAX,
    BIO_MAX,
    Profile,
)
from .validators import (
    CONTACT_CLEANERS,
    validate_no_angle_brackets,
    validate_person_name,
)

PRIVACY_FIELDS = (
    "show_location",
    "show_university",
    "show_contacts",
    "show_in_search",
    "show_join_date",
)


class CodeListField(serializers.ListField):
    """Список кодов из справочника: коды проверяются, повторы и лишние элементы запрещены."""

    def __init__(self, choice_list, max_items, **kwargs):
        super().__init__(child=serializers.ChoiceField(choices=choice_list), **kwargs)
        self.max_items = max_items

    def to_internal_value(self, data):
        items = super().to_internal_value(data)
        if len(items) > self.max_items:
            raise serializers.ValidationError(f"Choose up to {self.max_items}.", code="too_many")
        if len(set(items)) != len(items):
            raise serializers.ValidationError("Duplicate values are not allowed.", code="duplicate")
        return items


class ContactField(serializers.CharField):
    """Необязательный контакт: пустая строка допустима, иначе формат проверяет cleaner."""

    def __init__(self, cleaner, **kwargs):
        super().__init__(required=False, allow_blank=True, max_length=200, **kwargs)
        self.cleaner = cleaner

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if not value:
            return ""
        try:
            return self.cleaner(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0], code=exc.code) from None


class ContactsSerializer(serializers.Serializer):
    telegram = ContactField(CONTACT_CLEANERS["telegram"])
    instagram = ContactField(CONTACT_CLEANERS["instagram"])
    whatsapp = ContactField(CONTACT_CLEANERS["whatsapp"])
    linkedin = ContactField(CONTACT_CLEANERS["linkedin"])
    public_email = ContactField(CONTACT_CLEANERS["public_email"])


class ProfileFieldsSerializer(serializers.Serializer):
    """Поля профиля, которые человек вводит при регистрации и может менять в /api/me/."""

    first_name = serializers.CharField(max_length=60, validators=[validate_person_name])
    last_name = serializers.CharField(max_length=60, validators=[validate_person_name])
    gender = serializers.ChoiceField(choices=choices.GENDERS, required=False, allow_blank=True)
    country = serializers.ChoiceField(choices=choices.COUNTRIES)
    region = serializers.CharField(max_length=100, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    status = serializers.ChoiceField(choices=choices.STATUSES)
    school = serializers.CharField(max_length=100, required=False, allow_blank=True)
    university = serializers.CharField(
        max_length=120, required=False, allow_blank=True, validators=[validate_no_angle_brackets]
    )
    field = serializers.ChoiceField(choices=choices.FIELDS)
    year_level = serializers.CharField(max_length=40, required=False, allow_blank=True)
    bio = serializers.CharField(max_length=BIO_MAX, required=False, allow_blank=True)
    interests = CodeListField(choices.INTERESTS, INTERESTS_MAX, required=False)
    languages = CodeListField(choices.LANGUAGES, LANGUAGES_MAX, required=False)
    goals = CodeListField(choices.GOALS, GOALS_MAX, required=False)
    contacts = ContactsSerializer(required=False)

    def validate_bio(self, value):
        return value.replace("\r\n", "\n")


def forbid_minor_contacts(contacts, birth_date):
    """Младше ADULT_AGE любые контакты запрещены: ошибка поля contacts."""
    if contacts and any(contacts.values()) and calculate_age(birth_date) < settings.ADULT_AGE:
        error = ErrorDetail("Contacts are available from age 18.", code="not_allowed_for_minors")
        raise serializers.ValidationError({"contacts": [error]})


class OwnProfileSerializer(serializers.ModelSerializer):
    """Профиль для самого владельца (GET /api/me/ и ответ входа): включает личные поля."""

    email = serializers.EmailField(source="user.email", read_only=True)
    email_verified = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    is_minor = serializers.SerializerMethodField()
    contacts = serializers.SerializerMethodField()
    privacy = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            "email",
            "email_verified",
            "username",
            "first_name",
            "last_name",
            "date_of_birth",
            "age",
            "is_minor",
            "gender",
            "country",
            "region",
            "city",
            "status",
            "school",
            "university",
            "field",
            "year_level",
            "bio",
            "interests",
            "languages",
            "goals",
            "contacts",
            "avatar_url",
            "privacy",
            "created_at",
        )
        read_only_fields = fields

    def get_email_verified(self, obj):
        return obj.user.email_verified_at is not None

    def get_age(self, obj):
        return obj.age()

    def get_is_minor(self, obj):
        return obj.is_minor()

    def get_contacts(self, obj):
        return {name: getattr(obj, name) for name in CONTACT_FIELDS}

    def get_privacy(self, obj):
        return {name: getattr(obj, name) for name in PRIVACY_FIELDS}

    def get_avatar_url(self, obj):
        return None  # загрузка аватара появится позже


class MeUpdateSerializer(ProfileFieldsSerializer):
    """PATCH /api/me/: частичное обновление (serializer создаётся с partial=True)."""

    def validate(self, attrs):
        contacts = attrs.get("contacts")
        if contacts is not None:
            profile = self.instance
            merged = {name: getattr(profile, name) for name in CONTACT_FIELDS}
            merged.update(contacts)  # меняются только присланные контакты
            forbid_minor_contacts(merged, profile.date_of_birth)
            attrs["contacts"] = merged
        return attrs

    def update(self, profile, validated_data):
        contacts = validated_data.pop("contacts", {})
        for name, value in {**validated_data, **contacts}.items():
            setattr(profile, name, value)
        profile.save()
        return profile
