from django.conf import settings
from django.db import models


class Question(models.Model):
    TOPIC_CHOICES = [
        ("numbers", "Sonlar va amallar"),
        ("algebra", "Algebra"),
        ("equations", "Tenglama va tengsizliklar"),
        ("functions", "Funksiyalar"),
        ("analysis", "Hosila va integral"),
        ("probability", "Ehtimollar va statistika"),
        ("geometry", "Geometriya"),
    ]
    LEVEL_CHOICES = [
        ("easy", "Oson"),
        ("medium", "O‘rta"),
        ("hard", "Murakkab"),
    ]
    SOURCE_CHOICES = [
        ("curated", "Tahrirlangan savol"),
        ("official_sample", "Rasmiy namunaga asoslangan"),
        ("ai", "AI yaratgan"),
    ]

    topic = models.CharField(max_length=24, choices=TOPIC_CHOICES, db_index=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, db_index=True)
    text = models.TextField()
    options = models.JSONField(default=list)
    correct_index = models.PositiveSmallIntegerField()
    explanation = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="curated")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["topic", "level", "id"]

    def __str__(self):
        return f"{self.get_topic_display()} — {self.text[:65]}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if not isinstance(self.options, list) or len(self.options) < 2:
            raise ValidationError({"options": "Kamida 2 ta javob varianti bo‘lishi kerak."})
        if self.correct_index >= len(self.options):
            raise ValidationError({"correct_index": "To‘g‘ri javob indeksi variantlar sonidan katta."})


class Attempt(models.Model):
    MODE_CHOICES = [("practice", "Mavzuli mashq"), ("exam", "To‘liq imtihon")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="math_attempts")
    mode = models.CharField(max_length=12, choices=MODE_CHOICES)
    topic = models.CharField(max_length=24, blank=True)
    level = models.CharField(max_length=10, blank=True)
    total = models.PositiveSmallIntegerField(default=0)
    correct = models.PositiveSmallIntegerField(default=0)
    percent = models.PositiveSmallIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    answers = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.correct}/{self.total}"
