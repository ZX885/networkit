from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Учётная запись: вход по email. Данные профиля лежат в profiles.Profile."""

    # unique=True нужен Django для USERNAME_FIELD; регистронезависимость — констрейнт ниже
    email = models.EmailField(max_length=254, unique=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)  # null — почта не подтверждена
    # Новый адрес, ожидающий подтверждения по ссылке (смена email); email меняется только после подтверждения
    pending_email = models.EmailField(max_length=254, null=True, blank=True)

    # Модерация (меняется только в админке)
    is_banned = models.BooleanField(default=False)
    banned_at = models.DateTimeField(null=True, blank=True)
    ban_reason = models.CharField(max_length=200, blank=True)

    is_staff = models.BooleanField(default=False)  # доступ в Django Admin
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    # is_superuser, groups, user_permissions — из PermissionsMixin; last_login — из AbstractBaseUser

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [
            # A@x.com и a@x.com — один и тот же адрес
            models.UniqueConstraint(
                Lower("email"),
                name="users_user_email_lower_unique",
                violation_error_message="A user with this email already exists.",
            ),
        ]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.email = UserManager.normalize_email(self.email)
        super().save(*args, **kwargs)
