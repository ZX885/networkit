"""Справочники для клиента: GET /api/meta/. Источник правды — choices.py и settings; frontend
берёт списки отсюда. Ответ собирается один раз при запуске сервера и меняется только с деплоем."""

import hashlib
import json

from django.conf import settings

from . import choices
from .models import BIO_MAX, GOALS_MAX, INTERESTS_MAX, LANGUAGES_MAX


def build_meta():
    return {
        "countries": choices.as_options(choices.COUNTRIES),
        "fields": choices.as_options(choices.FIELDS),
        "statuses": choices.as_options(choices.STATUSES),
        "genders": choices.as_options(choices.GENDERS),
        "interests": choices.as_options(choices.INTERESTS),
        "languages": choices.as_options(choices.LANGUAGES),
        "goals": choices.as_options(choices.GOALS),
        "cities": choices.as_options(choices.UZ_CITIES),  # города страны country_cities_default
        "country_cities_default": choices.COUNTRY_CITIES_DEFAULT,
        "report_reasons": [],  # жалобы появятся позже (шаг про Report)
        "limits": {
            "bio_max": BIO_MAX,
            "min_age": settings.MIN_AGE,
            "adult_age": settings.ADULT_AGE,
            "interests_max": INTERESTS_MAX,
            "languages_max": LANGUAGES_MAX,
            "goals_max": GOALS_MAX,
            "saved_max": settings.SAVED_MAX,
        },
    }


def meta_etag(meta):
    """Слабый ETag по содержимому: клиент получает 304, пока справочники не изменились."""
    raw = json.dumps(meta, sort_keys=True, ensure_ascii=False).encode()
    return f'"{hashlib.sha256(raw).hexdigest()[:16]}"'
