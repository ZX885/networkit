"""Блокировки и жалобы. Блокировка работает в обе стороны, но заблокированный о ней не узнаёт
(см. rules.py). Тексты жалоб видны только суперпользователям в Django Admin."""

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from .choices import REPORT_REASONS


class Block(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks_made"
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks_received"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["blocker", "blocked"], name="block_pair_unique"),
            models.CheckConstraint(condition=~Q(blocker=F("blocked")), name="block_not_self"),
        ]
        indexes = [
            # «кто заблокировал меня» ищется по blocked; «кого заблокировал я» — по уникальному (blocker, blocked)
            models.Index(fields=["blocked", "blocker"], name="block_blocked_blocker_idx"),
            models.Index(fields=["blocker", "-created_at"], name="block_blocker_created_idx"),
        ]

    def __str__(self):
        return f"{self.blocker_id} blocks {self.blocked_id}"


class Report(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        DISMISSED = "dismissed", "Dismissed"
        ACTIONED = "actioned", "Actioned"

    # Автор остаётся null, если его аккаунт удалён: жалоба сохраняется
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="reports_made",
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_received"
    )
    # Жалоба на диалог: ссылка, а не копия текста (модератор открывает переписку в админке)
    conversation = models.ForeignKey(
        "messaging.Conversation", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    details = models.CharField(max_length=1000, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    staff_note = models.CharField(max_length=500, blank=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    handled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~Q(reporter=F("target")), name="report_not_self"),
            # Одна открытая жалоба от человека на человека (повторные не плодятся)
            models.UniqueConstraint(
                fields=["reporter", "target"],
                condition=Q(status="open"),
                name="report_one_open_per_pair",
            ),
        ]
        indexes = [models.Index(fields=["target", "status"], name="report_target_status_idx")]

    def __str__(self):
        return f"report {self.pk}: {self.reason} on {self.target_id}"
