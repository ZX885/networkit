"""Фабричные функции для тестов (сигналов нет, профиль создаётся явно)."""

import itertools
from datetime import date, timedelta

from apps.profiles.models import Profile
from apps.users.models import User

_counter = itertools.count(1)


def years_before(day, years):
    """Та же дата на `years` лет раньше (29 февраля → 28 февраля, если года не високосный)."""
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return day.replace(year=day.year - years, day=28)


def birth_date_for_age(age, days_short=0, today=None):
    """Дата рождения человека, которому сегодня ровно `age` полных лет (день рождения сегодня).

    days_short=1 — до `age`-летия остался 1 день: человеку пока age - 1 (граница «накануне»).
    """
    today = today or date.today()
    return years_before(today, age) + timedelta(days=days_short)


def make_user(email=None, password=None, **extra):
    # password=None → «неиспользуемый» пароль без хэширования: тесты профилей идут быстрее
    email = email or f"user{next(_counter)}@example.com"
    return User.objects.create_user(email=email, password=password, **extra)


def make_profile(user=None, **overrides):
    """Сохранённый профиль совершеннолетнего человека с корректными данными."""
    number = next(_counter)
    data = {
        "username": f"person{number}",
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": birth_date_for_age(25),
        "country": "UZ",
        "city": "Tashkent",
        "status": "student",
        "field": "computer_science",
    }
    data.update(overrides)
    return Profile.objects.create(user=user or make_user(), **data)
