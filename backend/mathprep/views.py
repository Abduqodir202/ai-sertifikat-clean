import json
import random
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from .models import Attempt, Question


EXAM_COUNT = 45
EXAM_SECONDS = 150 * 60


@ensure_csrf_cookie
def math_page(request):
    return render(request, "mathprep/index.html", {
        "exam_count": EXAM_COUNT,
        "exam_minutes": EXAM_SECONDS // 60,
    })


def _public_question(q):
    # To'g'ri javob mijozga test yakunlanmaguncha yuborilmaydi.
    return {
        "id": q.id,
        "topic": q.topic,
        "topic_label": q.get_topic_display(),
        "level": q.level,
        "level_label": q.get_level_display(),
        "text": q.text,
        "options": q.options,
        "source": q.source,
        "source_label": q.get_source_display(),
    }


@require_GET
def questions_api(request):
    mode = request.GET.get("mode", "practice")
    qs = Question.objects.filter(is_active=True)
    if mode == "exam":
        # Imtihon savollari barcha mavzu va darajalardan tanlanadi.
        questions = list(qs)
        if len(questions) < EXAM_COUNT:
            return JsonResponse({
                "error": f"Imtihon uchun kamida {EXAM_COUNT} ta faol savol kerak. Hozir: {len(questions)} ta."
            }, status=400)
        selected = random.sample(questions, EXAM_COUNT)
        random.shuffle(selected)
        return JsonResponse({
            "mode": "exam", "duration_seconds": EXAM_SECONDS,
            "questions": [_public_question(q) for q in selected]
        })

    topic = request.GET.get("topic", "all")
    level = request.GET.get("level", "all")
    if topic != "all":
        qs = qs.filter(topic=topic)
    if level != "all":
        qs = qs.filter(level=level)
    questions = list(qs)
    random.shuffle(questions)
    questions = questions[:20]
    return JsonResponse({
        "mode": "practice",
        "questions": [_public_question(q) for q in questions]
    })


@csrf_protect
@require_POST
def submit_attempt(request):
    try:
        payload = json.loads(request.body or "{}")
        question_ids = [int(x) for x in payload.get("question_ids", [])]
        submitted = payload.get("answers", {})
        mode = payload.get("mode", "practice")
        if mode not in ("practice", "exam") or not question_ids:
            return JsonResponse({"error": "So‘rov ma’lumotlari noto‘g‘ri."}, status=400)
        if len(question_ids) > 100:
            return JsonResponse({"error": "Savollar soni chegaradan oshdi."}, status=400)
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "JSON ma’lumotlarini tekshiring."}, status=400)

    qs = Question.objects.filter(id__in=question_ids, is_active=True)
    question_map = {str(q.id): q for q in qs}
    if len(question_map) != len(set(question_ids)):
        return JsonResponse({"error": "Savollardan biri topilmadi yoki faol emas."}, status=400)

    correct = 0
    details = []
    safe_answers = {}
    for qid in question_ids:
        q = question_map[str(qid)]
        raw = submitted.get(str(qid))
        try:
            chosen = int(raw) if raw is not None else None
        except (TypeError, ValueError):
            chosen = None
        is_correct = chosen == q.correct_index
        if is_correct:
            correct += 1
        safe_answers[str(qid)] = chosen
        details.append({
            "id": q.id,
            "chosen": chosen,
            "correct_index": q.correct_index,
            "is_correct": is_correct,
            "explanation": q.explanation,
            "correct_text": q.options[q.correct_index],
        })

    total = len(question_ids)
    percent = round(correct * 100 / total) if total else 0
    elapsed = max(0, min(int(payload.get("duration_seconds", 0)), EXAM_SECONDS * 3))
    attempt_id = None
    if request.user.is_authenticated:
        attempt = Attempt.objects.create(
            user=request.user,
            mode=mode,
            topic=payload.get("topic", "")[:24],
            level=payload.get("level", "")[:10],
            total=total,
            correct=correct,
            percent=percent,
            duration_seconds=elapsed,
            answers=safe_answers,
        )
        attempt_id = attempt.id

    return JsonResponse({
        "total": total, "correct": correct, "wrong": total - correct,
        "percent": percent, "details": details, "attempt_id": attempt_id,
        "saved": bool(attempt_id),
    })


@login_required
@require_GET
def attempt_history(request):
    attempts = Attempt.objects.filter(user=request.user)[:30]
    return JsonResponse({"items": [{
        "id": a.id, "mode": a.get_mode_display(), "total": a.total,
        "correct": a.correct, "percent": a.percent,
        "created_at": a.created_at.strftime("%d.%m.%Y %H:%M"),
    } for a in attempts]})


@csrf_protect
@require_POST
def ai_generate(request):
    if not getattr(settings, "OPENAI_API_KEY", ""):
        return JsonResponse({"error": "AI savol yaratish uchun OPENAI_API_KEY sozlanmagan."}, status=503)
    try:
        payload = json.loads(request.body or "{}")
        topic = payload.get("topic", "algebra")
        level = payload.get("level", "medium")
        count = max(1, min(int(payload.get("count", 5)), 10))
        valid_topics = {x[0] for x in Question.TOPIC_CHOICES}
        valid_levels = {x[0] for x in Question.LEVEL_CHOICES}
        if topic not in valid_topics or level not in valid_levels:
            return JsonResponse({"error": "Mavzu yoki daraja noto‘g‘ri."}, status=400)
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "So‘rov ma’lumotlari noto‘g‘ri."}, status=400)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=getattr(settings, "OPENAI_MATH_MODEL", "gpt-4o-mini"),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": (
                    "Siz matematika testlari tuzuvchisiz. O'zbek tilida aniq, tekshiriladigan "
                    "4 variantli savollar yarating. Rasmiy imtihon savoli deb da'vo qilmang. "
                    "Faqat JSON qaytaring: {questions:[{text,options:[A,B,C,D],"
                    "correct_index:0,explanation}]}. To'g'ri javob indeksini tekshiring."
                )},
                {"role": "user", "content": f"{count} ta {level} darajadagi {topic} savoli yarating."}
            ],
            temperature=0.4,
        )
        data = json.loads(response.choices[0].message.content)
        created = []
        for item in data.get("questions", [])[:count]:
            options = item.get("options", [])
            index = int(item.get("correct_index", -1))
            if not item.get("text") or len(options) != 4 or not 0 <= index < 4:
                continue
            q = Question.objects.create(
                topic=topic, level=level, text=item["text"],
                options=options, correct_index=index,
                explanation=item.get("explanation", ""),
                source="ai", is_active=True,
            )
            created.append(_public_question(q))
        return JsonResponse({"created": len(created), "questions": created})
    except Exception:
        # API kaliti, provayder javobi yoki ichki xatolarni oshkor qilmaymiz.
        return JsonResponse({"error": "AI savol yaratishda xatolik yuz berdi. Server loglarini tekshiring."}, status=502)
