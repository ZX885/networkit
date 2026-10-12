from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils import timezone

from .forms import UserChangeForm, UserCreationForm
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    ordering = ("email",)
    list_display = ("email", "is_active", "is_staff", "is_banned", "email_verified_at", "date_joined")
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

    @admin.action(description="Ban selected users")
    def ban_users(self, request, queryset):
        count = queryset.filter(is_banned=False).update(is_banned=True, banned_at=timezone.now())
        self.message_user(request, f"Banned users: {count}", messages.SUCCESS)

    @admin.action(description="Unban selected users")
    def unban_users(self, request, queryset):
        count = queryset.filter(is_banned=True).update(is_banned=False, banned_at=None)
        self.message_user(request, f"Unbanned users: {count}", messages.SUCCESS)
