"""Переписка в Django Admin: ТОЛЬКО чтение и ТОЛЬКО для суперпользователей (владельцев сайта).
Обычный staff модуль не видит; добавлять, менять и удалять нельзя. Тела сообщений выводятся только в
карточке сообщения (для суперпользователя) и нигде не логируются: просмотр не создаёт записей
LogEntry, приложение не пишет текст сообщений в журналы. Об этом нужно сказать в Privacy Policy."""

from django.contrib import admin

from .models import Conversation, Message


class SuperuserReadOnlyAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(SuperuserReadOnlyAdmin):
    list_display = ("id", "user_a", "user_b", "initiator", "status", "last_message_at")
    list_filter = ("status",)
    list_select_related = ("user_a", "user_b", "initiator")
    ordering = ("-last_message_at",)


@admin.register(Message)
class MessageAdmin(SuperuserReadOnlyAdmin):
    # В списке текста нет: он виден только в карточке сообщения
    list_display = ("id", "conversation", "sender", "created_at", "seen_at")
    list_select_related = ("sender",)
    ordering = ("-id",)
