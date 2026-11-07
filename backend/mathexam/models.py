import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

class ExamQuestion(models.Model):
    DIFFICULTY = [("easy","Oson"),("medium","O‘rta"),("hard","Qiyin")]
    text = models.TextField("Savol")
    option_a = models.CharField("A", max_length=500)
    option_b = models.CharField("B", max_length=500)
    option_c = models.CharField("C", max_length=500)
    option_d = models.CharField("D", max_length=500)
    correct_option = models.CharField(max_length=1, choices=[(x,x) for x in "ABCD"])
    explanation = models.TextField("Yechim izohi", blank=True)
    topic = models.CharField("Mavzu", max_length=120, blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY, default="medium")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "Imtihon savoli"
        verbose_name_plural = "Imtihon savollari"
    def __str__(self):
        return f"{self.pk}. {self.text[:70]}"

class ExamAttempt(models.Model):
    STATUS = [("in_progress","Jarayonda"),("submitted","Yakunlangan")]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    session_key = models.CharField(max_length=64, db_index=True)
    question_ids = models.JSONField(default=list)
    answers = models.JSONField(default=dict)
    started_at = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="in_progress")
    correct_count = models.PositiveSmallIntegerField(default=0)
    wrong_count = models.PositiveSmallIntegerField(default=0)
    unanswered_count = models.PositiveSmallIntegerField(default=0)
    percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Imtihon urinishi"
        verbose_name_plural = "Imtihon urinishlari"
