"""python manage.py seed_demo_profiles [--count 20] [--delete]

Создаёт вымышленных подтверждённых пользователей для демо и ручной проверки поиска.
Все данные выдуманы: почта demo-N@example.invalid (такой домен не существует), пароль
не задан (войти под ними нельзя). --delete удаляет только созданных этой командой.

При DEBUG=False команда ничего не делает без флага --i-know-this-is-a-demo: на боевом сайте
демо-данные нельзя оставлять (на Railway запускать только для показа и затем удалять --delete).
"""

import random
import re
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.profiles import choices
from apps.profiles.age import calculate_age
from apps.profiles.models import Profile
from apps.users.models import User

DEMO_EMAIL = "demo-{n}@example.invalid"
DEMO_EMAIL_REGEX = r"^demo-([0-9]+)@example\.invalid$"
CONFIRM_FLAG = "--i-know-this-is-a-demo"

FIRST_NAMES = [
    "Amina", "Timur", "Sofia", "Daniyar", "Laura", "Rustam", "Mei", "Omar", "Nilufar", "Lucas",
    "Zarina", "James", "Elif", "Ivan", "Dilnoza", "Carlos", "Aigul", "Noah", "Madina", "Leo",
    "Aisha", "Bekzod", "Hana", "Pavel", "Yuki", "Sara", "Jasur", "Emma", "Ali", "Maria",
]
LAST_NAMES = [
    "Karimova", "Bekov", "Martins", "Seitkali", "Hansen", "Aliev", "Chen", "Haddad", "Rakhimova",
    "Ferreira", "Tursunova", "Okafor", "Yilmaz", "Petrov", "Yusupova", "Garcia", "Nurlan", "Smith",
    "Abdullaeva", "Kim", "Sato", "Novak", "Ismailov", "Rossi", "Khan", "Dubois", "Olsen", "Lopez",
]
# Другие страны → города (Узбекистан берёт города из apps/profiles/choices.py)
CITIES = {
    "KZ": ["Almaty", "Astana"],
    "KG": ["Bishkek", "Osh"],
    "TR": ["Istanbul", "Ankara"],
    "DE": ["Berlin", "Munich"],
    "FR": ["Paris", "Lyon"],
    "BR": ["Sao Paulo", "Rio de Janeiro"],
    "IN": ["Delhi", "Mumbai"],
}
OTHER_COUNTRIES = ["KZ", "KG", "TR", "DE", "FR", "BR", "IN"]
# Города Узбекистана вне справочника (в форме это вариант «Other»)
UZ_OTHER_CITIES = ["Zomin", "Chust", "Kitab", "Yangiyer"]
UNIVERSITIES = ["WIUT", "TSUL", "SamSU", "AUCA", "Nazarbayev University", "TU Berlin", "METU"]
SCHOOLS = ["Lyceum 5", "School 110", "Presidential School", "IT Lyceum", "Gymnasium 3"]
YEAR_LEVELS_STUDENT = ["1st year", "2nd year", "3rd year", "4th year", "Master 1st year"]
YEAR_LEVELS_PRO = ["Junior", "Middle", "Senior", "Lead"]
BIOS = [
    "Studying {field} and looking for people to build side projects with.",
    "Into {field}. Always happy to swap notes and ideas.",
    "Working in {field}. Open to mentoring and to being mentored.",
    "Curious about {field}; trying to meet people from other countries.",
    "Learning {field} and preparing for the next step. Say hi!",
]


class Command(BaseCommand):
    help = "Создаёт (или с --delete удаляет) вымышленных пользователей для демо и теста поиска."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=20, help="Сколько людей создать (по умолчанию 20).")
        parser.add_argument("--delete", action="store_true", help="Удалить созданных этой командой.")
        parser.add_argument(
            CONFIRM_FLAG,
            action="store_true",
            dest="confirm_demo",
            help="Разрешить запуск при DEBUG=False (только для демо с вымышленными данными).",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["confirm_demo"]:
            raise CommandError(
                "DEBUG=False: команда не запущена. Это демо-данные, на боевом сайте их быть не должно. "
                f"Для демонстрации добавьте {CONFIRM_FLAG}, после показа удалите через --delete."
            )
        if options["delete"]:
            self.delete_demo()
            return
        if options["count"] < 1:
            raise CommandError("--count должен быть не меньше 1.")
        self.create_demo(options["count"])

    def demo_users(self):
        return User.objects.filter(email__regex=DEMO_EMAIL_REGEX)

    def delete_demo(self):
        # Профиль удаляется каскадом вместе с пользователем
        deleted, _ = self.demo_users().delete()
        self.stdout.write(self.style.SUCCESS(f"Удалено записей (пользователи и профили): {deleted}."))

    def next_number(self):
        numbers = [
            int(re.match(DEMO_EMAIL_REGEX, email).group(1))
            for email in self.demo_users().values_list("email", flat=True)
        ]
        return max(numbers, default=0) + 1

    @transaction.atomic
    def create_demo(self, count):
        start = self.next_number()
        for n in range(start, start + count):
            self.create_one(n)
        self.stdout.write(
            self.style.SUCCESS(
                f"Создано {count} демо-профилей (demo-{start}…demo-{start + count - 1}@example.invalid)."
            )
        )

    def create_one(self, n):
        rng = random.Random(n)  # одно и то же число даёт одного и того же человека
        today = timezone.localdate()
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        is_minor = n % 5 == 0  # каждый пятый младше 18
        age = rng.randint(settings.MIN_AGE, settings.ADULT_AGE - 1) if is_minor else rng.randint(18, 45)
        birth = today - timedelta(days=age * 365 + rng.randint(0, 364))
        if calculate_age(birth, today) != age:  # день рождения мог «сдвинуться» из-за високосных лет
            birth = today - timedelta(days=age * 366 + 1)
        # Место: 70% — города Узбекистана из справочника, 10% — другой город Узбекистана («Other»),
        # 20% — другие страны (так фильтр по городу есть на чём показать)
        slot = n % 10
        if slot <= 6:
            country, city = "UZ", rng.choice(choices.UZ_CITIES)[1]
        elif slot == 7:
            country, city = "UZ", rng.choice(UZ_OTHER_CITIES)
        else:
            country = rng.choice(OTHER_COUNTRIES)
            city = rng.choice(CITIES[country])
        is_student = is_minor or rng.random() < 0.6
        field = rng.choice(choices.FIELDS)
        adult_with_contacts = (not is_minor) and rng.random() < 0.5

        user = User.objects.create_user(
            email=DEMO_EMAIL.format(n=n), password=None, email_verified_at=timezone.now()
        )
        profile = Profile(
            user=user,
            username=f"{first.lower()}_{last[0].lower()}{n}",
            first_name=first,
            last_name=last,
            date_of_birth=birth,
            gender=rng.choice(["male", "female", "non_binary", "undisclosed", ""]),
            country=country,
            city=city,
            status="student" if is_student else "professional",
            school=rng.choice(SCHOOLS) if is_minor else "",
            university=rng.choice(UNIVERSITIES) if (is_student and not is_minor and rng.random() < 0.8) else "",
            field=field[0],
            year_level=rng.choice(YEAR_LEVELS_STUDENT if is_student else YEAR_LEVELS_PRO),
            bio=rng.choice(BIOS).format(field=field[1]),
            interests=rng.sample(choices.codes(choices.INTERESTS), rng.randint(1, 5)),
            languages=rng.sample(choices.codes(choices.LANGUAGES), rng.randint(1, 3)),
            goals=rng.sample(choices.codes(choices.GOALS), rng.randint(1, 3)),
            # Приватность: часть людей скрывает город, вуз, участие в поиске и дату регистрации
            show_location=rng.random() >= 0.25,
            show_university=rng.random() >= 0.25,
            show_in_search=rng.random() >= 0.12,
            show_join_date=rng.random() >= 0.10,
            # Контакты — только у части взрослых; несовершеннолетним нельзя ни хранить, ни показывать
            show_contacts=adult_with_contacts and rng.random() < 0.7,
            telegram=f"{first.lower()}_{n}" if adult_with_contacts else "",
            public_email=f"{first.lower()}{n}@example.invalid" if adult_with_contacts else "",
        )
        profile.full_clean()
        profile.save()
        # Даты регистрации разбрасываем, чтобы сортировка «новые первыми» была заметна
        Profile.objects.filter(pk=profile.pk).update(
            created_at=timezone.now() - timedelta(days=rng.randint(0, 60), minutes=rng.randint(0, 1439))
        )
