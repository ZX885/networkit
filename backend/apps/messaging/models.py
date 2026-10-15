"""Личные сообщения: диалог двух людей (с запросом на переписку) и сообщения в нём.

Тексты сообщений хранятся как есть (без HTML-обработки). Владельцы сайта (суперпользователи) могут
читать переписку в Django Admin (только чтение) — это должно быть указано в Privacy Policy.
"""

import uuid

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """Диалог пары людей. Пара хранится упорядоченно (user_a_id < user_b_id), поэтому на пару
    возможен только один диалог. initiator — кто отправил запрос на переписку."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # непредсказуемый
    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_a"
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_b"
    )
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="initiated_conversations"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    decided_at = models.DateTimeField(null=True, blank=True)  # когда получатель принял/отклонил
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(user_a__lt=models.F("user_b")), name="conv_users_ordered"
            ),
            models.UniqueConstraint(fields=["user_a", "user_b"], name="conv_pair_unique"),
            # инициатор — один из двух участников
            models.CheckConstraint(
                condition=models.Q(initiator=models.F("user_a"))
                | models.Q(initiator=models.F("user_b")),
                name="conv_initiator_is_member",
            ),
        ]
        indexes = [
            models.Index(fields=["user_a", "-last_message_at"], name="conv_a_last_idx"),
            models.Index(fields=["user_b", "-last_message_at"], name="conv_b_last_idx"),
        ]

    def __str__(self):
        return f"{self.pk}"

    @property
    def recipient_id(self):
        """Кто получает запрос (второй участник, не инициатор)."""
        return self.user_b_id if self.initiator_id == self.user_a_id else self.user_a_id

    def is_member(self, user):
        return user.pk in (self.user_a_id, self.user_b_id)

    def other_id(self, user):
        return self.user_b_id if user.pk == self.user_a_id else self.user_a_id


class Message(models.Model):
    """Сообщение. sender — участник диалога (проверяется в сервисе отправки: условие «автор —
    участник» в БД ограничением CHECK не выразить, оно требует данных другой таблицы)."""

    id = models.BigAutoField(primary_key=True)  # возрастает: курсор выдачи
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    seen_at = models.DateTimeField(null=True, blank=True)  # ставит получатель через /read/

    class Meta:
        indexes = [models.Index(fields=["conversation", "created_at"], name="msg_conv_created_idx")]

    def __str__(self):
        # Тело сообщения нигде не выводим (логи, админка-список): только номера
        return f"message {self.pk} in {self.conversation_id}"
