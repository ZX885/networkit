from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Менеджер пользователей с входом по email (email всегда хранится в нижнем регистре)."""

    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        # Стандартная версия понижает регистр только у домена; нам нужен весь адрес
        return (email or "").strip().lower()

    def get_by_natural_key(self, email):
        # Вход в админку и authenticate(): регистр введённого email не важен
        return self.get(email=self.normalize_email(email))

    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # сохраняется хэш, не пароль
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields["is_staff"] is not True or extra_fields["is_superuser"] is not True:
            raise ValueError("Superuser must have is_staff=True and is_superuser=True")
        return self._create_user(email, password, **extra_fields)
