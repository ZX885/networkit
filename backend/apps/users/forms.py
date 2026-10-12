from django.contrib.auth.forms import BaseUserCreationForm
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm

from .models import User


class UserCreationForm(BaseUserCreationForm):
    """Создание пользователя в админке: email и пароль (сохраняется хэш)."""

    class Meta:
        model = User
        fields = ("email",)


class UserChangeForm(BaseUserChangeForm):
    """Изменение пользователя: пароль показан как хэш (только чтение), меняется отдельной ссылкой."""

    class Meta:
        model = User
        fields = "__all__"
