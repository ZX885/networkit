from django.contrib import admin

from .models import Profile, SavedProfile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Дата рождения в список не выводится (личные данные); в форме она видна только staff
    list_display = ("username", "first_name", "last_name", "country", "status", "created_at")
    list_filter = ("status", "country")
    search_fields = ("username", "first_name", "last_name", "user__email")
    raw_id_fields = ("user",)  # поле выбора без огромного выпадающего списка
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(SavedProfile)
class SavedProfileAdmin(admin.ModelAdmin):
    """Закладки только для просмотра: ни добавлять, ни менять, ни удалять через админку нельзя."""

    list_display = ("owner", "saved_user", "created_at")
    list_select_related = ("owner", "saved_user")
    search_fields = ("owner__email", "saved_user__email")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
