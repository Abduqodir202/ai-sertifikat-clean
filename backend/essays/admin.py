from django.contrib import admin
from .models import Essay
from datetime import timedelta

from django.utils import timezone

from .models import UnlimitedAccess



@admin.register(Essay)
class EssayAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "topic",
        "total_score",
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "topic",
    )
    list_filter = ("created_at",)
    ordering = ("-created_at",)




@admin.register(UnlimitedAccess)
class UnlimitedAccessAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "is_active",
        "activated_at",
        "expires_at",
        "status",
    )
    list_filter = ("is_active",)
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user",)
    readonly_fields = ("activated_at", "expires_at")

    @admin.display(description="Holati")
    def status(self, obj):
        if (
            obj.is_active
            and obj.expires_at
            and obj.expires_at > timezone.now()
        ):
            return "Faol"
        return "Faol emas"

    def save_model(self, request, obj, form, change):
        was_active = False

        if change:
            previous = UnlimitedAccess.objects.get(pk=obj.pk)
            was_active = (
                previous.is_active
                and previous.expires_at is not None
                and previous.expires_at > timezone.now()
            )

        if obj.is_active and not was_active:
            now = timezone.now()
            obj.activated_at = now
            obj.expires_at = now + timedelta(days=30)

        elif not obj.is_active:
            obj.activated_at = None
            obj.expires_at = None

        super().save_model(request, obj, form, change)
