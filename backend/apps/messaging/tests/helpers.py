"""Общие помощники тестов сообщений."""

from apps.messaging.models import Conversation, Message
from apps.users.tests.helpers import make_account

CONVERSATIONS = "/api/conversations/"

CONVERSATION_KEYS = {
    "id",
    "other_user",
    "status",
    "initiated_by_me",
    "last_message",
    "unread_count",
    "last_message_at",
    "created_at",
}
OTHER_USER_KEYS = {"username", "first_name", "last_name", "avatar_url", "field_label"}
LAST_MESSAGE_KEYS = {"body", "sender_is_me", "created_at"}
MESSAGE_KEYS = {"id", "sender_is_me", "body", "created_at", "seen_at"}


def person(username, **profile):
    """Подтверждённый человек: почта <username>@example.com."""
    return make_account(email=f"{username}@example.com", username=username, **profile)


def send_request(client, username, body="Hi there!"):
    return client.post(CONVERSATIONS, {"username": username, "body": body}, format="json")


def make_conversation(initiator, other, status=Conversation.Status.PENDING, first_body="Hello!"):
    """Диалог в базе (в обход API) с первым сообщением от инициатора."""
    user_a, user_b = sorted([initiator, other], key=lambda user: user.pk)
    conversation = Conversation.objects.create(
        user_a=user_a, user_b=user_b, initiator=initiator, status=status
    )
    if first_body is not None:
        message = Message.objects.create(conversation=conversation, sender=initiator, body=first_body)
        Conversation.objects.filter(pk=conversation.pk).update(last_message_at=message.created_at)
    return conversation


def add_message(conversation, sender, body="text", seen=False):
    from django.utils import timezone

    message = Message.objects.create(
        conversation=conversation, sender=sender, body=body, seen_at=timezone.now() if seen else None
    )
    Conversation.objects.filter(pk=conversation.pk).update(last_message_at=message.created_at)
    return message


def url(conversation, suffix=""):
    return f"{CONVERSATIONS}{conversation.pk}/{suffix}"
