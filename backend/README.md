# AI Sertifikat — Matematika moduli

Django ilovasi: `mathprep`. Mavzuli mashqlar, darajalar, 45 savolli/150 daqiqalik imtihon, natijalarni saqlash va ixtiyoriy OpenAI orqali savol yaratish.

## 1. O'rnatish

Loyiha ildizida:

```bash
pip install openai
python manage.py startapp mathprep
```

Ushbu paketdagi `mathprep/` papkasini loyiha ildiziga ko'chiring (startapp yaratgan papkani almashtiring).

`settings.py` ichiga:

```python
INSTALLED_APPS = [
    # ...
    "mathprep",
]

# OpenAI orqali savol yaratish ixtiyoriy:
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
```

Agar `environ` ishlatmasangiz:

```python
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
```

Asosiy `urls.py` ichiga:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("matematika/", include("mathprep.urls")),
]
```

## 2. Migratsiya va savollarni yuklash

```bash
python manage.py makemigrations mathprep
python manage.py migrate
python manage.py seed_math_questions
```

## 3. Sahifa

`http://127.0.0.1:8000/matematika/`

Template `base.html` dan meros oladi. Agar sizning loyihangizda asosiy template boshqa joyda bo'lsa, `templates/mathprep/index.html` ichidagi `{% extends "base.html" %}` qatorini moslang.

## 4. AI savol yaratish

Admin yoki frontenddagi "AI savol yaratish" tugmasi `/matematika/api/ai-generate/` endpointiga so'rov yuboradi. `OPENAI_API_KEY` bo'lmasa, tugma foydalanuvchiga tushunarli xatolik qaytaradi. AI yaratgan savollar `source="ai"` deb belgilanadi va avtomatik ravishda rasmiy savol deb ko'rsatilmaydi.

## 5. Muhim eslatma

45 savol / 150 daqiqa bu moduldagi mashq imtihoni konfiguratsiyasi. Uni amaldagi rasmiy spetsifikatsiya bilan tekshirib tasdiqlang. Ushbu kod foiz va to'g'ri javoblar sonini hisoblaydi; Rasch modeli bo'yicha rasmiy ball bermaydi.
