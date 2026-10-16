"""Общие помощники тестов модерации."""

from apps.moderation.models import Block
from apps.users.tests.helpers import make_account

BLOCKS = "/api/blocks/"
REPORTS = "/api/reports/"
SEARCH = "/api/profiles/"
SAVED = "/api/saved/"
SECRET = "SECRET-report-text-7731"

MINI_CARD_KEYS = {"username", "first_name", "last_name", "avatar_url"}


def person(username, **profile):
    """Подтверждённый человек: почта <username>@example.com."""
    return make_account(email=f"{username}@example.com", username=username, **profile)


def block(blocker, blocked):
    return Block.objects.create(blocker=blocker, blocked=blocked)


def usernames(response):
    return [item["username"] for item in response.json()["results"]]
