"""Модерация в Django Admin: ТОЛЬКО для суперпользователей (владельцев сайта).

Жалобы: текст и участников менять нельзя, редактируются только статус и заметка модератора
(handled_by / handled_at ставятся автоматически). Сначала идут жалобы «underage» и «harassment»,
внутри группы — новые. В карточке видны число открытых жалоб на ту же цель и список других жалоб на неё
(только дата, причина и статус: без чужих текстов). Блокировки — только чтение."""

from django.contrib import admin, messages
from django.db.models import Case, Count, IntegerField, OuterRef, Subquery, Value, When
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join

from apps.messaging.admin import SuperuserReadOnlyAdmin
from apps.users.services import delete_user_sessions

from .choices import URGENT_REASONS
from .models import Block, Report

OTHER_REPORTS_SHOWN = 20


class SuperuserOnlyMixin:
    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PriorityFilter(admin.SimpleListFilter):
    title = "priority"
    parameter_name = "priority"

    def lookups(self, request, model_admin):
        return [("urgent", "Urgent (underage, harassment)"), ("other", "Other reasons")]

    def queryset(self, request, queryset):
        if self.value() == "urgent":
            return queryset.filter(reason__in=URGENT_REASONS)
        if self.value() == "other":
            return queryset.exclude(reason__in=URGENT_REASONS)
        return queryset


@admin.register(Report)
class ReportAdmin(SuperuserOnlyMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "reason",
        "target",
        "reporter",
        "status",
        "open_on_target",
        "has_conversation",
    )
    list_display_links = ("id", "created_at")
    list_filter = (PriorityFilter, "status", "reason")
    search_fields = ("target__email", "target__profile__username", "reporter__email")
    list_select_related = ("target", "reporter")
    actions = ["mark_dismissed", "mark_actioned", "ban_target_users"]

    fieldsets = (
        ("Report", {"fields": ("created_at", "reason", "details", "reporter", "target", "conversation_link")}),
        ("Same person", {"fields": ("open_on_target", "other_reports")}),
        ("Moderation", {"fields": ("status", "staff_note", "handled_by", "handled_at")}),
    )
    readonly_fields = (
        "created_at",
        "reason",
        "details",
        "reporter",
        "target",
        "conversation_link",
        "open_on_target",
        "other_reports",
        "handled_by",
        "handled_at",
    )

    def get_queryset(self, request):
        """Аннотации одним запросом: приоритет для сортировки и число открытых жалоб на ту же цель."""
        open_on_same_target = (
            Report.objects.filter(target=OuterRef("target"), status=Report.Status.OPEN)
            .order_by()
            .values("target")
            .annotate(total=Count("pk"))
            .values("total")
        )
        # Не super(): ModelAdmin.get_queryset применяет get_ordering() ещё до аннотаций
        return self.model._default_manager.get_queryset().annotate(
            priority=Case(
                When(reason__in=URGENT_REASONS, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            open_on_target_count=Subquery(open_on_same_target, output_field=IntegerField()),
        )

    def get_ordering(self, request):
        return ("priority", "-created_at", "-id")  # underage и harassment первыми, внутри — новые

    # ── колонки и поля только для чтения ──

    @admin.display(description="Open on this person", ordering="open_on_target_count")
    def open_on_target(self, obj):
        count = getattr(obj, "open_on_target_count", None)
        if count is None:  # объект без аннотации (например, только что созданный)
            count = Report.objects.filter(target_id=obj.target_id, status=Report.Status.OPEN).count()
        return count or 0

    @admin.display(boolean=True, description="Conversation")
    def has_conversation(self, obj):
        return obj.conversation_id is not None

    @admin.display(description="Conversation")
    def conversation_link(self, obj):
        if obj.conversation_id is None:
            return "—"
        url = reverse("admin:messaging_conversation_change", args=[obj.conversation_id])
        return format_html('<a href="{}">Open conversation (read-only)</a>', url)

    @admin.display(description="Other reports on this person")
    def other_reports(self, obj):
        """Дата, причина и статус других жалоб на ту же цель; текстов и авторов нет."""
        rows = list(
            Report.objects.filter(target_id=obj.target_id)
            .exclude(pk=obj.pk)
            .order_by("-created_at", "-id")
            .values_list("pk", "created_at", "reason", "status")[:OTHER_REPORTS_SHOWN]
        )
        if not rows:
            return "—"
        return format_html(
            "<ul>{}</ul>",
            format_html_join(
                "",
                '<li><a href="{}">#{}</a> — {} — {} — {}</li>',
                (
                    (
                        reverse("admin:moderation_report_change", args=[pk]),
                        pk,
                        created.strftime("%Y-%m-%d %H:%M"),
                        reason,
                        status,
                    )
                    for pk, created, reason, status in rows
                ),
            ),
        )

    # ── автоматические поля ──

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            self._stamp(obj, request.user)
        super().save_model(request, obj, form, change)

    @staticmethod
    def _stamp(report, staff):
        if report.status == Report.Status.OPEN:
            report.handled_by, report.handled_at = None, None
        else:
            report.handled_by, report.handled_at = staff, timezone.now()

    # ── действия ──

    def _set_status(self, request, queryset, new_status):
        count = queryset.exclude(status=new_status).update(
            status=new_status, handled_by=request.user, handled_at=timezone.now()
        )
        self.message_user(request, f"Reports updated: {count}", messages.SUCCESS)

    @admin.action(description="Mark dismissed")
    def mark_dismissed(self, request, queryset):
        self._set_status(request, queryset, Report.Status.DISMISSED)

    @admin.action(description="Mark actioned")
    def mark_actioned(self, request, queryset):
        self._set_status(request, queryset, Report.Status.ACTIONED)

    @admin.action(description="Ban target user (ends their sessions, marks actioned)")
    def ban_target_users(self, request, queryset):
        from apps.users.models import User

        target_ids = list(queryset.values_list("target_id", flat=True).distinct())
        # Суперпользователей этим действием не баним
        users = User.objects.filter(pk__in=target_ids, is_superuser=False)
        banned = users.filter(is_banned=False).update(is_banned=True, banned_at=timezone.now())
        sessions = delete_user_sessions(list(users.values_list("pk", flat=True)))
        actioned = queryset.exclude(status=Report.Status.ACTIONED).update(
            status=Report.Status.ACTIONED, handled_by=request.user, handled_at=timezone.now()
        )
        self.message_user(
            request,
            f"Banned users: {banned}. Sessions ended: {sessions}. Reports actioned: {actioned}",
            messages.SUCCESS,
        )


@admin.register(Block)
class BlockAdmin(SuperuserReadOnlyAdmin):
    list_display = ("id", "blocker", "blocked", "created_at")
    list_select_related = ("blocker", "blocked")
    ordering = ("-created_at",)
    search_fields = ("blocker__email", "blocked__email")
