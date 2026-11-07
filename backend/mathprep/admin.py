from django.contrib import admin
from .models import Attempt, Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "topic", "level", "source", "is_active", "created_at")
    list_filter = ("topic", "level", "source", "is_active")
    search_fields = ("text", "explanation")
    list_editable = ("is_active",)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "mode", "correct", "total", "percent", "created_at")
    list_filter = ("mode", "created_at")
    search_fields = ("user__username",)
    readonly_fields = ("user", "mode", "topic", "level", "total", "correct", "percent",
                       "duration_seconds", "answers", "created_at")
