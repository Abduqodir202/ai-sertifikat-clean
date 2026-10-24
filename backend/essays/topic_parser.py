import json
import re
from typing import Dict

from django.conf import settings
from openai import OpenAI


# ============================================================
# AI SERTIFIKAT
# OCR TEXT → TOPIC + ESSAY
# AI SEMANTIC PARSER
# ============================================================


def normalize_text(text: str) -> str:
    """
    OCR orqali olingan matnni tozalaydi.
    """

    if not text:
        return ""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Ortiqcha bo'shliqlar
    text = re.sub(r"[ \t]+", " ", text)

    # 3 yoki undan ko'p bo'sh qatorlarni 2 taga tushiramiz
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_json_from_response(content: str) -> Dict:
    """
    AI javobidan JSONni xavfsiz ajratib oladi.
    """

    if not content:
        raise ValueError("AI bo'sh javob qaytardi.")

    content = content.strip()

    # ```json ... ``` bo'lsa, olib tashlaymiz
    content = re.sub(
        r"^```json\s*",
        "",
        content,
        flags=re.IGNORECASE
    )

    content = re.sub(
        r"^```\s*",
        "",
        content
    )

    content = re.sub(
        r"\s*```$",
        "",
        content
    )

    content = content.strip()

    # To'g'ridan-to'g'ri JSON
    try:
        result = json.loads(content)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    # Javob ichidan {...} qismini topishga harakat qilamiz
    start = content.find("{")
    end = content.rfind("}")

    if start != -1 and end != -1 and end > start:
        json_text = content[start:end + 1]

        try:
            result = json.loads(json_text)

            if isinstance(result, dict):
                return result

        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"AI noto'g'ri JSON qaytardi: {content[:500]}"
    )


def validate_result(result: Dict, original_text: str) -> Dict:
    """
    AI qaytargan topic va essayni tekshiradi.
    """

    topic = result.get("topic", "")
    essay = result.get("essay", "")

    if topic is None:
        topic = ""

    if essay is None:
        essay = ""

    topic = str(topic).strip()
    essay = str(essay).strip()

    # Agar AI essayni qaytarmagan bo'lsa,
    # original OCR matnidan foydalanamiz.
    if not essay:
        essay = original_text.strip()

    return {
        "topic": topic,
        "essay": essay,
        "method": "ai_semantic",
        "topic_word_count": len(topic.split()),
        "essay_word_count": len(essay.split()),
        "topic_character_count": len(topic),
        "essay_character_count": len(essay),
    }


def split_topic_and_essay_with_ai(text: str) -> Dict:
    """
    OCR orqali olingan bitta umumiy matndan
    AI yordamida MAVZU va ESSEni ajratadi.

    Masalan:

    Тема:
    Нужно ли человеку уметь признавать свои ошибки?

    Каждый человек в жизни совершает ошибки...

    Natija:

    {
        "topic": "Нужно ли человеку уметь признавать свои ошибки?",
        "essay": "Каждый человек в жизни совершает ошибки..."
    }
    """

    text = normalize_text(text)

    if not text:
        return {
            "topic": "",
            "essay": "",
            "method": "empty",
            "topic_word_count": 0,
            "essay_word_count": 0,
            "topic_character_count": 0,
            "essay_character_count": 0,
        }

    # ========================================================
    # OPENAI CLIENT
    # ========================================================

    api_key = getattr(settings, "OPENAI_API_KEY", None)

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY settings.py da topilmadi."
        )

    client = OpenAI(api_key=api_key)

    # ========================================================
    # AI PROMPT
    # ========================================================

    system_prompt = """
Ты являешься модулем обработки текста для системы
проверки эссе "AI Sertifikat".

Твоя задача — получить OCR-текст изображения или PDF,
в котором одновременно могут находиться:

1. ТЕМА эссе
2. ТЕКСТ ЭССЕ

Ты должен семантически определить, какая часть является
темой, а какая частью эссе.

ВАЖНЫЕ ПРАВИЛА:

1. Не придумывай тему.
2. Не изменяй смысл темы.
3. Не переписывай тему своими словами.
4. Если в OCR есть "Тема:", "Тема", "Задание:",
   "Вопрос:" и т.п., используй это как дополнительный
   ориентир.
5. Если слово "Тема" отсутствует, самостоятельно определи
   тему по смыслу и структуре текста.
6. Обычно тема находится перед эссе.
7. Тема может быть вопросом.
8. Тема может быть утверждением.
9. Тема может состоять из нескольких строк.
10. Эссе может состоять из нескольких абзацев.
11. Не удаляй и не сокращай содержание эссе.
12. Не исправляй орфографические ошибки эссе.
13. Сохраняй оригинальный текст эссе максимально точно.
14. OCR может содержать ошибки. Не используй OCR-ошибки
    как причину для изменения текста.
15. Если тему невозможно надежно определить,
    верни пустую строку в поле "topic".
16. В поле "essay" верни весь доступный текст эссе.
17. Никаких комментариев вне JSON.

Верни ТОЛЬКО JSON следующего формата:

{
    "topic": "точный текст темы",
    "essay": "полный текст эссе"
}
"""

    user_prompt = f"""
Проанализируй следующий OCR-текст.

Определи:
- где находится тема;
- где начинается и заканчивается эссе.

Не придумывай отсутствующий текст.

OCR TEXT:
--------------------
{text}
--------------------

Верни только JSON:

{{
    "topic": "...",
    "essay": "..."
}}
"""

    # ========================================================
    # OPENAI REQUEST
    # ========================================================

    response = client.chat.completions.create(
        model=getattr(
            settings,
            "OPENAI_TOPIC_MODEL",
            "gpt-4o-mini"
        ),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    content = response.choices[0].message.content

    result = extract_json_from_response(content)

    return validate_result(result, text)


# ============================================================
# UNIVERSAL FUNCTION
# ============================================================

def parse_ocr_text(text: str) -> Dict:
    """
    OCR text → AI semantic topic + essay parser.

    Bu funksiyani views.py ichidan chaqirish mumkin.
    """

    return split_topic_and_essay_with_ai(text)