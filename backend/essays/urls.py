from django.urls import path

from .views import (
    CheckEssayAPIView,
    OCRAPIView,
    EssayUsageAPIView,
)

urlpatterns = [
    path(
        "check-essay/",
        CheckEssayAPIView.as_view(),
        name="check-essay",
    ),
    path(
        "ocr/",
        OCRAPIView.as_view(),
        name="ocr",
    ),
    path(
        "essay-usage/",
        EssayUsageAPIView.as_view(),
        name="essay-usage",
    ),
]
