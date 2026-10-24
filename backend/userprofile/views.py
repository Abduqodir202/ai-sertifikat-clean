from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

from .forms import RegisterForm
from essays.models import Essay


@require_GET
def my_profile(request):
    """Tizimga kirgan foydalanuvchi profilini qaytaradi."""

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "authenticated": False,
                "message": "Avval tizimga kiring.",
            },
            status=401,
        )

    user = request.user

    return JsonResponse(
        {
            "authenticated": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            },
        }
    )


@require_GET
def my_essays(request):
    """Faqat tizimga kirgan foydalanuvchining esselarini qaytaradi."""

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "authenticated": False,
                "message": "Avval tizimga kiring.",
            },
            status=401,
        )

    essays = Essay.objects.filter(
        user=request.user
    ).order_by("-created_at")

    results = []

    for essay in essays:
        results.append(
            {
                "id": essay.id,
                "topic": essay.topic,
                "student_name": essay.student_name,
                "word_count": essay.word_count,
                "character_count": essay.character_count,
                "paragraph_count": essay.paragraph_count,
                "total_score": essay.total_score,
                "ai_review": essay.ai_review,
                "created_at": essay.created_at.isoformat(),
            }
        )

    return JsonResponse(
        {
            "authenticated": True,
            "count": len(results),
            "essays": results,
        }
    )


def register_view(request):
    """Yangi foydalanuvchini ro‘yxatdan o‘tkazadi."""

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend",
            )

            return redirect("home")
    else:
        form = RegisterForm()

    return render(
        request,
        "userprofile/register.html",
        {"form": form},
    )


@login_required(login_url="/accounts/login/")
def profile_page(request):
    """Profil va esselar statistikasini ko‘rsatadi."""

    essays = Essay.objects.filter(
        user=request.user
    ).order_by("-created_at")

    # Barcha esselar ichidan eng yuqori ball
    best_essay = essays.order_by("-total_score", "-created_at").first()

    return render(
        request,
        "html/profile.html",
        {
            "essays": essays,
            "profile_user": request.user,
            "essays_count": essays.count(),
            "best_score": best_essay.total_score if best_essay else 0,
        },
    )


@login_required(login_url="/accounts/login/")
def essay_detail_page(request, essay_id):
    """Bitta essening batafsil natijasini ko‘rsatadi."""

    essay = get_object_or_404(
        Essay,
        id=essay_id,
        user=request.user,
    )

    criteria = [
        {
            "name": "Раскрытие темы (содержание)",
            "score": essay.criterion_1,
            "max_score": 20,
            "reason": essay.criterion_1_reason,
        },
        {
            "name": "Аргументация и примеры",
            "score": essay.criterion_2,
            "max_score": 15,
            "reason": essay.criterion_2_reason,
        },
        {
            "name": "Структура и логика",
            "score": essay.criterion_3,
            "max_score": 10,
            "reason": essay.criterion_3_reason,
        },
        {
            "name": "Лексика и стилистика",
            "score": essay.criterion_4,
            "max_score": 10,
            "reason": essay.criterion_4_reason,
        },
        {
            "name": "Грамотность",
            "score": essay.criterion_5,
            "max_score": 10,
            "reason": essay.criterion_5_reason,
        },
        {
            "name": "Оригинальность (самостоятельность мысли)",
            "score": essay.criterion_6,
            "max_score": 10,
            "reason": essay.criterion_6_reason,
        },
    ]

    return render(
        request,
        "html/essay-detail.html",
        {
            "essay": essay,
            "criteria": criteria,
        },
    )
