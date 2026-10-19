from types import SimpleNamespace

from django.contrib.auth import password_validation
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from apps.profiles.models import Profile
from apps.profiles.serializers import ProfileFieldsSerializer, forbid_minor_contacts
from apps.profiles.validators import validate_birth_date, validate_username


class RegisterSerializer(ProfileFieldsSerializer):
    """Тело POST /api/auth/register/ (docs/SPEC.md §3.2): аккаунт + поля профиля.

    Лишние ключи (phone, field_other и т.п.) молча игнорируются.
    """

    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)
    username = serializers.CharField(max_length=30)
    date_of_birth = serializers.DateField(validators=[validate_birth_date])
    accepted_terms = serializers.BooleanField()

    def validate_email(self, value):
        return value.strip().lower()

    def validate_username(self, value):
        username = value.strip().lower()  # имя хранится в нижнем регистре
        validate_username(username)  # формат и зарезервированные имена
        if Profile.objects.filter(username=username).exists():
            raise serializers.ValidationError("This username is already taken.", code="taken")
        return username

    def validate_password(self, value):
        # Проверка «пароль слишком похож на email/имя» берёт данные из присланного запроса,
        # поэтому ошибки пароля видны сразу вместе с остальными, а не на втором круге
        data = self.initial_data
        person = SimpleNamespace(
            email=str(data.get("email", "")).strip().lower(),
            username=str(data.get("username", "")).strip().lower(),
            first_name=str(data.get("first_name", "")).strip(),
            last_name=str(data.get("last_name", "")).strip(),
            # Валидатору «похож на данные пользователя» нужно имя поля для текста ошибки
            _meta=SimpleNamespace(get_field=lambda name: SimpleNamespace(verbose_name=name)),
        )
        password_validation.validate_password(value, user=person)
        return value

    def validate_accepted_terms(self, value):
        if value is not True:
            error = ErrorDetail("You must accept the Terms and Privacy Policy.", code="required")
            raise serializers.ValidationError(error)
        return value

    def validate(self, attrs):
        forbid_minor_contacts(attrs.get("contacts"), attrs["date_of_birth"])
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, trim_whitespace=False)

    def validate_email(self, value):
        return value.strip().lower()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        return value.strip().lower()


class NewPasswordSerializer(serializers.Serializer):
    """Новый пароль (сброс по ссылке): полные проверки с учётом данных пользователя из context["user"]."""

    new_password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)

    def validate_new_password(self, value):
        from . import services

        services.validate_new_password(value, self.context["user"])
        return value


def _check_current_password(user, value):
    if not user.check_password(value):
        raise serializers.ValidationError("Incorrect password.", code="incorrect")
    return value


class PasswordChangeSerializer(NewPasswordSerializer):
    """POST /api/auth/password/change/: старый пароль и новый."""

    old_password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)

    def validate_old_password(self, value):
        return _check_current_password(self.context["user"], value)

    def validate(self, attrs):
        # Новый пароль не может совпадать со старым (старый уже проверен как верный)
        if attrs["new_password"] == attrs["old_password"]:
            raise serializers.ValidationError(
                {"new_password": [ErrorDetail("The new password must be different from the current one.", code="same_as_old")]}
            )
        return attrs


class EmailChangeSerializer(serializers.Serializer):
    """POST /api/auth/email/change/: новый адрес и текущий пароль."""

    new_email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)

    def validate_new_email(self, value):
        return value.strip().lower()

    def validate_password(self, value):
        return _check_current_password(self.context["user"], value)


class DeleteAccountSerializer(serializers.Serializer):
    """DELETE /api/me/: пароль подтверждает удаление."""

    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)

    def validate_password(self, value):
        return _check_current_password(self.context["user"], value)
