from django.contrib import admin
from .models import ExamQuestion, ExamAttempt
@admin.register(ExamQuestion)
class ExamQuestionAdmin(admin.ModelAdmin):
    list_display=("id","topic","difficulty","correct_option","is_active")
    list_filter=("topic","difficulty","is_active")
    search_fields=("text","explanation")
    list_editable=("is_active",)
@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display=("public_id","user","status","correct_count","percent","started_at")
    readonly_fields=[f.name for f in ExamAttempt._meta.fields]
