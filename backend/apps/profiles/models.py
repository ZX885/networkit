from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models
from django.db.models.functions import Length

from . import choices
from .age import calculate_age
from .validators import (
    USERNAME_REGEX,
    validate_birth_date,
    validate_unique_items,
    validate_username,
)

BIO_MAX = 300
INTERESTS_MAX = 10
LANGUAGES_MAX = 10
GOALS_MAX = 8

# Контакты: несовершеннолетним (младше ADULT_AGE) запрещены
CONTACT_FIELDS = ("telegram", "instagram", "whatsapp", "linkedin", "public_email")


def code_list(choice_list, size):
    """Список кодов из справочника: коды проверяются, повторы и превышение лимита запрещены."""
    return ArrayField(
        models.CharField(max_length=30, choices=choice_list),
        size=size,
        default=list,
        blank=True,
        validators=[validate_unique_items],
    )


def array_size_limit(field_name, limit, name):
    """Ограничение БД: в массиве не больше limit элементов (cardinality — число элементов)."""
    size = models.Func(
        models.F(field_name), function="cardinality", output_field=models.IntegerField()
    )
    return models.CheckConstraint(condition=models.lookups.LessThanOrEqual(size, limit), name=name)


class Profile(models.Model):
    """Публичные данные человека. Создаётся явно (в API регистрации), сигналов нет."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    username = models.CharField(max_length=30, unique=True, validators=[validate_username])
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    date_of_birth = models.DateField(validators=[validate_birth_date])  # другим пользователям не показывается
    gender = models.CharField(max_length=20, choices=choices.GENDERS, blank=True)

    country = models.CharField(max_length=2, choices=choices.COUNTRIES)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)

    status = models.CharField(max_length=12, choices=choices.STATUSES)
    school = models.CharField(max_length=100, blank=True)
    university = models.CharField(max_length=120, blank=True)
    field = models.CharField(max_length=40, choices=choices.FIELDS)  # «Other» — код other
    year_level = models.CharField(max_length=40, blank=True)

    bio = models.TextField(blank=True, validators=[MaxLengthValidator(BIO_MAX)])
    interests = code_list(choices.INTERESTS, INTERESTS_MAX)
    languages = code_list(choices.LANGUAGES, LANGUAGES_MAX)
    goals = code_list(choices.GOALS, GOALS_MAX)

    # Контакты (необязательные; форматы проверят сериализаторы в B3)
    telegram = models.CharField(max_length=32, blank=True)
    instagram = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    linkedin = models.CharField(max_length=200, blank=True)
    public_email = models.EmailField(max_length=254, blank=True)

    # Приватность: что видят другие пользователи
    show_location = models.BooleanField(default=True)
    show_university = models.BooleanField(default=True)
    show_contacts = models.BooleanField(default=False)
    show_in_search = models.BooleanField(default=True)
    show_join_date = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["country"], name="profile_country_idx"),
            models.Index(fields=["field"], name="profile_field_idx"),
            models.Index(fields=["status"], name="profile_status_idx"),
            GinIndex(fields=["interests"], name="profile_interests_gin"),
            GinIndex(fields=["languages"], name="profile_languages_gin"),
            GinIndex(fields=["goals"], name="profile_goals_gin"),
        ]
        constraints = [
            # Те же правила, что в валидаторах, но на уровне базы (защита от записи в обход full_clean)
            models.CheckConstraint(
                condition=models.Q(username__regex=USERNAME_REGEX)
                & ~models.Q(username__contains="__"),
                name="profile_username_format",
            ),
            models.CheckConstraint(
                condition=models.lookups.LessThanOrEqual(Length("bio"), BIO_MAX),
                name="profile_bio_max_length",
            ),
            array_size_limit("interests", INTERESTS_MAX, "profile_interests_max"),
            array_size_limit("languages", LANGUAGES_MAX, "profile_languages_max"),
            array_size_limit("goals", GOALS_MAX, "profile_goals_max"),
        ]

    def __str__(self):
        return self.username

    def age(self, today=None):
        """Полных лет (today нужен для тестов на границах)."""
        return calculate_age(self.date_of_birth, today)

    def is_minor(self, today=None):
        """Младше ADULT_AGE (18 лет)."""
        return self.age(today) < settings.ADULT_AGE

    def clean(self):
        super().clean()
        # Несовершеннолетним нельзя ни хранить контакты, ни открывать их другим
        if self.date_of_birth and self.is_minor():
            message = "Contacts are available from age 18."
            errors = {
                name: ValidationError(message, code="not_allowed_for_minors")
                for name in CONTACT_FIELDS
                if getattr(self, name)
            }
            if self.show_contacts:
                errors["show_contacts"] = ValidationError(message, code="not_allowed_for_minors")
            if errors:
                raise ValidationError(errors)
