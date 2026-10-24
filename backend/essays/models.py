from django.db import models
from django.contrib.auth.models import User


class Essay(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="essays"
    )

    essay_text = models.TextField()
    topic = models.TextField(blank=True, default="")
    student_name = models.CharField(
        max_length=150,
        blank=True,
        default=""
    )

    word_count = models.PositiveIntegerField(default=0)
    character_count = models.PositiveIntegerField(default=0)
    paragraph_count = models.PositiveIntegerField(default=0)

    total_score = models.FloatField(default=0)

    criterion_1 = models.FloatField(default=0)
    criterion_2 = models.FloatField(default=0)
    criterion_3 = models.FloatField(default=0)
    criterion_4 = models.FloatField(default=0)
    criterion_5 = models.FloatField(default=0)
    criterion_6 = models.FloatField(default=0)
    criterion_7 = models.FloatField(default=0)
    criterion_8 = models.FloatField(default=0)
    criterion_9 = models.FloatField(default=0)
    criterion_10 = models.FloatField(default=0)
    criterion_11 = models.FloatField(default=0)
    criterion_12 = models.FloatField(default=0)
    criterion_1_reason = models.TextField(blank=True, default="")
    criterion_2_reason = models.TextField(blank=True, default="")
    criterion_3_reason = models.TextField(blank=True, default="")
    criterion_4_reason = models.TextField(blank=True, default="")
    criterion_5_reason = models.TextField(blank=True, default="")
    criterion_6_reason = models.TextField(blank=True, default="")
    criterion_7_reason = models.TextField(blank=True, default="")
    criterion_8_reason = models.TextField(blank=True, default="")
    criterion_9_reason = models.TextField(blank=True, default="")
    criterion_10_reason = models.TextField(blank=True, default="")
    criterion_11_reason = models.TextField(blank=True, default="")
    criterion_12_reason = models.TextField(blank=True, default="")

    ai_review = models.TextField(blank=True, default="")

    errors = models.JSONField(
        default=list,
        blank=True
    )

    recommendations = models.JSONField(
        default=list,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.total_score}/75"



class UnlimitedAccess(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="unlimited_access",
    )
    is_active = models.BooleanField(default=False)
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Unlimited huquqi"
        verbose_name_plural = "Unlimited huquqlari"

    def __str__(self):
        return f"{self.user.username} — Unlimited"
