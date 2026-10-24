
import logging

from django.shortcuts import render
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Essay, UnlimitedAccess
from .ocr import file_to_text
from .topic_parser import parse_ocr_text
from .language_checker import detect_essay_language
from .ai_checker import check_essay_with_ai


logger = logging.getLogger(__name__)

MAX_TOTAL = 75
DAILY_ESSAY_LIMIT = 5

CRITERIA = [
    {
        "name": "Раскрытие темы (содержание)",
        "max_score": 20,
        "score_field": "criterion_1",
        "reason_field": "criterion_1_reason",
    },
    {
        "name": "Аргументация и примеры",
        "max_score": 15,
        "score_field": "criterion_2",
        "reason_field": "criterion_2_reason",
    },
    {
        "name": "Структура и логика",
        "max_score": 10,
        "score_field": "criterion_3",
        "reason_field": "criterion_3_reason",
    },
    {
        "name": "Лексика и стилистика",
        "max_score": 10,
        "score_field": "criterion_4",
        "reason_field": "criterion_4_reason",
    },
    {
        "name": "Грамотность",
        "max_score": 10,
        "score_field": "criterion_5",
        "reason_field": "criterion_5_reason",
    },
    {
        "name": "Оригинальность (самостоятельность мысли)",
        "max_score": 10,
        "score_field": "criterion_6",
        "reason_field": "criterion_6_reason",
    },
]


def api_error(message, http_status, **extra):
    """API uchun yagona xato javobi."""
    data = {"error": message}
    data.update(extra)
    return Response(data, status=http_status)


def clean_errors(errors, essay_text):
    """AI qaytargan xatolarni tekshiradi."""
    if not isinstance(errors, list):
        return []

    cleaned = []

    for error in errors:
        if not isinstance(error, dict):
            continue

        fragment = str(error.get("fragment") or "").strip()

        if not fragment or fragment not in essay_text:
            continue

        cleaned.append({
            "fragment": fragment,
            "type": str(
                error.get("type") or "Языковая ошибка"
            ).strip(),
            "correction": str(
                error.get("correction") or ""
            ).strip(),
            "explanation": str(
                error.get("explanation") or ""
            ).strip(),
        })

    return cleaned


def clean_recommendations(recommendations):
    """Tavsiyalarni bir xil formatga keltiradi."""
    if not isinstance(recommendations, list):
        return []

    cleaned = []

    for item in recommendations:
        if isinstance(item, dict):
            text = (
                item.get("text")
                or item.get("recommendation")
                or item.get("description")
                or ""
            )
        else:
            text = str(item or "")

        text = str(text).strip()

        if text:
            cleaned.append(text)

    return cleaned


def has_unlimited_access(user):
    """
    Foydalanuvchida muddati tugamagan Unlimited huquqi borligini tekshiradi.
    """
    now = timezone.now()

    return UnlimitedAccess.objects.filter(
        user=user,
        is_active=True,
        expires_at__gt=now,
    ).exists()


def get_daily_usage(user):
    """
    Bugun muvaffaqiyatli saqlangan esselar sonini hisoblaydi.
    """
    today = timezone.localdate()

    return Essay.objects.filter(
        user=user,
        created_at__date=today,
    ).count()


class CheckEssayAPIView(APIView):
    """
    Rus tilidagi esseni AI yordamida tekshiradi.

    Kunlik bepul limit: 5 ta esse.
    Faol Unlimited huquqi bo'lgan foydalanuvchi limit bilan cheklanmaydi.
    Har bir esse aynan tizimga kirgan foydalanuvchiga saqlanadi.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Foydalanuvchini tekshirish
        user = request.user

        if not user or not user.is_authenticated:
            return api_error(
                "Avval tizimga kiring.",
                status.HTTP_401_UNAUTHORIZED,
            )

        # 2. Kunlik limitni AI chaqirilishidan oldin tekshirish
        try:
            unlimited = has_unlimited_access(user)

            if not unlimited:
                used_today = get_daily_usage(user)
                remaining = max(
                    DAILY_ESSAY_LIMIT - used_today,
                    0,
                )

                if remaining <= 0:
                    return api_error(
                        "Bugungi 5 ta bepul esse tekshirish "
                        "limitingiz tugadi. Ertaga qayta urinib "
                        "ko'ring.",
                        status.HTTP_429_TOO_MANY_REQUESTS,
                        daily_limit=DAILY_ESSAY_LIMIT,
                        used_today=used_today,
                        remaining=0,
                    )

        except Exception:
            logger.exception(
                "Foydalanuvchi limitini tekshirishda xatolik"
            )
            return api_error(
                "Limitni tekshirishda xatolik yuz berdi.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 3. Foydalanuvchi yuborgan ma'lumotlar
        essay_text = request.data.get("essay", "")
        topic = request.data.get("topic", "")
        student_name = str(
            request.data.get("student_name") or ""
        ).strip()

        if not isinstance(essay_text, str):
            return api_error(
                "Essay matni noto'g'ri formatda.",
                status.HTTP_400_BAD_REQUEST,
            )

        essay_text = essay_text.strip()

        if not essay_text:
            return api_error(
                "Essay matni bo'sh.",
                status.HTTP_400_BAD_REQUEST,
            )

        if len(essay_text) > 20000:
            return api_error(
                "Essay matni 20000 belgidan oshmasligi kerak.",
                status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(topic, str):
            return api_error(
                "Essay mavzusi noto'g'ri formatda.",
                status.HTTP_400_BAD_REQUEST,
            )

        topic = topic.strip()

        if not topic:
            return api_error(
                "Essay mavzusini kiriting.",
                status.HTTP_400_BAD_REQUEST,
            )

        if len(topic) > 500:
            return api_error(
                "Essay mavzusi 500 belgidan oshmasligi kerak.",
                status.HTTP_400_BAD_REQUEST,
            )

        # 4. Matn statistikasi
        words = essay_text.split()
        word_count = len(words)
        character_count = len(essay_text)

        paragraphs = [
            paragraph.strip()
            for paragraph in essay_text.splitlines()
            if paragraph.strip()
        ]
        paragraph_count = len(paragraphs)

        # 5. Rus tilini tekshirish
        try:
            language_result = detect_essay_language(essay_text)

        except Exception:
            logger.exception(
                "Essay tilini aniqlashda xatolik"
            )
            return api_error(
                "Tilni aniqlashda xatolik yuz berdi.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not isinstance(language_result, dict):
            return api_error(
                "Til tekshiruvi noto'g'ri javob qaytardi.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not language_result.get("is_russian", False):
            return api_error(
                "Эссе должно быть написано на русском языке.",
                status.HTTP_400_BAD_REQUEST,
                language=language_result,
            )

        # 6. AI orqali tekshirish
        try:
            ai_result = check_essay_with_ai(
                essay_text=essay_text,
                topic=topic,
            )

        except ValueError as exc:
            return api_error(
                str(exc),
                status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            logger.exception("AI essay tekshiruvida xatolik")
            return api_error(
                "AI tekshiruvda xatolik yuz berdi.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not isinstance(ai_result, dict):
            return api_error(
                "AI noto'g'ri formatda javob qaytardi.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 7. Mavzu mosligini tekshirish
        topic_check = ai_result.get("topic_check")

        if not isinstance(topic_check, dict):
            return api_error(
                "AI mavzu tekshiruvi natijasini qaytarmadi.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        topic_valid = topic_check.get("valid")
        topic_match = topic_check.get("match")

        if not isinstance(topic_valid, bool):
            return api_error(
                "Mavzu tekshiruvi natijasi noto'g'ri.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if topic_match not in ("full", "partial", "none"):
            return api_error(
                "Mavzuga moslik qiymati noto'g'ri.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not topic_valid:
            return api_error(
                "Тема письменной работы некорректна.",
                status.HTTP_400_BAD_REQUEST,
                topic_check=topic_check,
            )

        if topic_match == "none":
            return api_error(
                "Эссе не соответствует теме.",
                status.HTTP_400_BAD_REQUEST,
                topic_check=topic_check,
            )

        # 8. Oltita baholash mezonini tekshirish
        criteria = ai_result.get("criteria")

        if not isinstance(criteria, list) or len(criteria) != 6:
            return api_error(
                "AI 6 ta baholash mezoni bo'yicha natija "
                "qaytarmadi.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        cleaned_criteria = []
        total_score = 0.0

        for index, (definition, criterion) in enumerate(
            zip(CRITERIA, criteria),
            start=1,
        ):
            if not isinstance(criterion, dict):
                return api_error(
                    f"{index}-mezon noto'g'ri formatda.",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            try:
                score = float(criterion.get("score"))
            except (TypeError, ValueError):
                return api_error(
                    f"{index}-mezon uchun ball noto'g'ri.",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            max_score = definition["max_score"]

            if (
                not 0 <= score <= max_score
                or not (score * 2).is_integer()
            ):
                return api_error(
                    f"{index}-mezon balli noto'g'ri. "
                    f"Ruxsat etilgan oraliq: 0–{max_score}, "
                    "qadam 0.5.",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            reason = str(
                criterion.get("reason") or ""
            ).strip()

            if not reason:
                return api_error(
                    f"{index}-mezon uchun izoh qaytarilmadi.",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            if score.is_integer():
                score = int(score)

            cleaned_criteria.append({
                "name": definition["name"],
                "score": score,
                "max_score": max_score,
                "reason": reason,
            })

            total_score += score

        if not 0 <= total_score <= MAX_TOTAL:
            return api_error(
                "Hisoblangan umumiy ball noto'g'ri.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if total_score.is_integer():
            total_score = int(total_score)

        # 9. Taqriz, xatolar va tavsiyalar
        ai_review = str(
            ai_result.get("review") or ""
        ).strip()

        errors = clean_errors(
            ai_result.get("errors", []),
            essay_text,
        )

        recommendations = clean_recommendations(
            ai_result.get("recommendations", [])
        )

        # 10. Natijani bazaga saqlash
        try:
            essay_fields = {
                "user": user,
                "essay_text": essay_text,
                "topic": topic,
                "student_name": student_name,
                "word_count": word_count,
                "character_count": character_count,
                "paragraph_count": paragraph_count,
                "total_score": total_score,
                "ai_review": ai_review,
                "errors": errors,
                "recommendations": recommendations,
            }

            for definition, criterion in zip(
                CRITERIA,
                cleaned_criteria,
            ):
                essay_fields[definition["score_field"]] = (
                    criterion["score"]
                )
                essay_fields[definition["reason_field"]] = (
                    criterion["reason"]
                )

            essay = Essay.objects.create(**essay_fields)

        except Exception:
            logger.exception("Essay bazaga saqlanmadi")
            return api_error(
                "Essayni bazaga saqlashda xatolik yuz berdi.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 11. Frontend uchun natija
        response_criteria = []

        for definition in CRITERIA:
            response_criteria.append({
                "name": definition["name"],
                "score": getattr(
                    essay,
                    definition["score_field"],
                ),
                "max_score": definition["max_score"],
                "reason": getattr(
                    essay,
                    definition["reason_field"],
                ),
            })

        # 12. Limit haqida ma'lumot
        if unlimited:
            limit_info = {
                "unlimited": True,
                "daily_limit": None,
                "used_today": None,
                "remaining": None,
            }
        else:
            used_today = get_daily_usage(user)
            limit_info = {
                "unlimited": False,
                "daily_limit": DAILY_ESSAY_LIMIT,
                "used_today": used_today,
                "remaining": max(
                    DAILY_ESSAY_LIMIT - used_today,
                    0,
                ),
            }

        return Response(
            {
                "id": essay.id,
                "total_score": essay.total_score,
                "max_score": MAX_TOTAL,
                "word_count": essay.word_count,
                "character_count": essay.character_count,
                "paragraph_count": essay.paragraph_count,
                "review": essay.ai_review,
                "topic_check": topic_check,
                "errors": essay.errors,
                "recommendations": essay.recommendations,
                "criteria": response_criteria,
                "usage": limit_info,
            },
            status=status.HTTP_200_OK,
        )


class OCRAPIView(APIView):
    """
    Rasm yoki PDF ichidagi matnni ajratadi.
    Faqat tizimga kirgan foydalanuvchi foydalanishi mumkin.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return api_error(
                "Fayl yuborilmadi.",
                status.HTTP_400_BAD_REQUEST,
            )

        allowed_extensions = (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".pdf",
        )
        filename = str(
            uploaded_file.name or ""
        ).lower()

        if not filename.endswith(allowed_extensions):
            return api_error(
                "Faqat JPG, PNG, WEBP yoki PDF fayllar qabul qilinadi.",
                status.HTTP_400_BAD_REQUEST,
            )

        # Katta fayllarni cheklash: 10 MB
        max_size = 10 * 1024 * 1024

        if uploaded_file.size > max_size:
            return api_error(
                "Fayl hajmi 10 MB dan oshmasligi kerak.",
                status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 1. Fayldan matn olish
            text = file_to_text(uploaded_file)

            print("\n=== OCR API ASL MATNI ===", flush=True)
            print(text, flush=True)
            print("=== OCR MATNI TUGADI ===\n", flush=True)

            if not text or not text.strip():
                return api_error(
                    "Fayldan matn topilmadi.",
                    status.HTTP_400_BAD_REQUEST,
                )

            text = text.strip()

            # 2. Mavzu va esseni ajratish
            parsed = parse_ocr_text(text)

            if not isinstance(parsed, dict):
                parsed = {}

            topic = str(
                parsed.get("topic") or ""
            ).strip()

            essay = str(
                parsed.get("essay") or ""
            ).strip()

            if not essay:
                essay = text

            # 3. Statistika
            word_count = len(essay.split())
            character_count = len(essay)

            if not essay.strip():
                return api_error(
                    "Rasmdan matn o'qilmadi. "
                    "Rasmni aniqroq qilib qayta yuklang.",
                    status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {
                    "text": text,
                    "topic": topic,
                    "essay": essay,
                    "word_count": word_count,
                    "character_count": character_count,
                    "topic_word_count": len(topic.split()),
                    "topic_character_count": len(topic),
                    "parser_method": parsed.get(
                        "method",
                        "ai_semantic",
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as exc:
            return api_error(
                str(exc),
                status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            logger.exception("OCR ishlashida xatolik")
            return api_error(
                "OCR ishlashida xatolik yuz berdi.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def ona_tili_page(request):
    return render(request, "ona-tili.html")


def matematika_page(request):
    return render(request, "matematika.html")



class EssayUsageAPIView(APIView):
    """Foydalanuvchining bugungi esse limitini qaytaradi."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            unlimited = has_unlimited_access(user)

            if unlimited:
                return Response({
                    "unlimited": True,
                    "daily_limit": None,
                    "used_today": None,
                    "remaining": None,
                })

            used_today = get_daily_usage(user)
            remaining = max(DAILY_ESSAY_LIMIT - used_today, 0)

            return Response({
                "unlimited": False,
                "daily_limit": DAILY_ESSAY_LIMIT,
                "used_today": used_today,
                "remaining": remaining,
            })

        except Exception:
            logger.exception("Esse limitini olishda xatolik")
            return api_error(
                "Limit ma'lumotlarini olishda xatolik yuz berdi.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
