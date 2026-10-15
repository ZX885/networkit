"""Ответы API сообщений (явные списки ключей: ничего лишнего, без email и даты рождения)."""

from rest_framework import serializers

from apps.profiles import choices
from apps.profiles.visibility import ProfileVisibility

from .models import Conversation

Status = Conversation.Status


class ConversationSerializer(serializers.BaseSerializer):
    """Диалог глазами зрителя (context["user"]): статус с маскированием, собеседник, последнее
    сообщение. Требует диалог, подготовленный queries.annotated()."""

    def to_representation(self, conversation):
        user = self.context["user"]
        other_user = conversation.user_b if conversation.user_a_id == user.pk else conversation.user_a
        profile = other_user.profile
        initiated_by_me = conversation.initiator_id == user.pk
        status = conversation.status
        if initiated_by_me and status == Status.DECLINED:
            status = Status.PENDING  # маскирование: инициатор не узнаёт об отказе
        last = None
        if conversation.last_created_at is not None:
            last = {
                "body": conversation.last_body,
                "sender_is_me": conversation.last_sender_id == user.pk,
                "created_at": conversation.last_created_at,
            }
        return {
            "id": str(conversation.pk),
            "other_user": {
                "username": profile.username,
                **ProfileVisibility(profile).name(),  # имя — через общую функцию visibility
                "avatar_url": None,
                "field_label": choices.label_of(choices.FIELDS, profile.field),
            },
            "status": status,
            "initiated_by_me": initiated_by_me,
            "last_message": last,
            "unread_count": conversation.unread_count,
            "last_message_at": conversation.last_message_at,
            "created_at": conversation.created_at,
        }


class MessageSerializer(serializers.BaseSerializer):
    def to_representation(self, message):
        user = self.context["user"]
        return {
            "id": message.pk,
            "sender_is_me": message.sender_id == user.pk,
            "body": message.body,
            "created_at": message.created_at,
            "seen_at": message.seen_at,
        }
