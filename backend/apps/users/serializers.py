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


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=1000)


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        return value.strip().lower()
