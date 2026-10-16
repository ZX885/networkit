from django.contrib import admin, messages
from django.db.models import Count, Q
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils import timezone

from .forms import UserChangeForm, UserCreationForm
from .models import User
from .services import delete_user_sessions


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    ordering = ("email",)
    list_display = (
        "email",
        "is_active",
        "is_staff",
        "is_banned",
        "open_reports",
        "email_verified_at",
        "date_joined",
    )
    list_filter = ("is_banned", "is_staff", "is_active")
    search_fields = ("email",)
    readonly_fields = ("banned_at", "last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Status", {"fields": ("is_active", "email_verified_at")}),
        ("Moderation", {"fields": ("is_banned", "banned_at", "ban_reason")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )

    actions = ["ban_users", "unban_users"]

    def get_queryset(self, request):
        # Число открытых жалоб на человека: один запрос с агрегатом на весь список
        return super().get_queryset(request).annotate(
            open_reports_count=Count("reports_received", filter=Q(reports_received__status="open"))
        )

    @admin.display(description="Open reports", ordering="open_reports_count")
    def open_reports(self, obj):
        return obj.open_reports_count

    @admin.action(description="Ban selected users")
    def ban_users(self, request, queryset):
        user_ids = list(queryset.values_list("pk", flat=True))
        count = queryset.filter(is_banned=False).update(is_banned=True, banned_at=timezone.now())
        sessions = delete_user_sessions(user_ids)  # забаненный сразу теряет вход
        self.message_user(
            request, f"Banned users: {count}. Sessions ended: {sessions}", messages.SUCCESS
        )

    @admin.action(description="Unban selected users")
    def unban_users(self, request, queryset):
        count = queryset.filter(is_banned=True).update(is_banned=False, banned_at=None)
        self.message_user(request, f"Unbanned users: {count}", messages.SUCCESS)
