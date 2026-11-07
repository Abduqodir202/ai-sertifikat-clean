from django.urls import path
from . import views

app_name = "mathprep"

urlpatterns = [
    path("", views.math_page, name="home"),
    path("api/questions/", views.questions_api, name="questions"),
    path("api/submit/", views.submit_attempt, name="submit"),
    path("api/history/", views.attempt_history, name="history"),
    path("api/ai-generate/", views.ai_generate, name="ai_generate"),
]
