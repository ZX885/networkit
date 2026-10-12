from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Дата рождения в список не выводится (личные данные); в форме она видна только staff
    list_display = ("username", "first_name", "last_name", "country", "status", "created_at")
    list_filter = ("status", "country")
    search_fields = ("username", "first_name", "last_name", "user__email")
    raw_id_fields = ("user",)  # поле выбора без огромного выпадающего списка
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
