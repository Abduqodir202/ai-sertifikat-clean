
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# OCR va Python kutubxonalari uchun tizim paketlari
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-uzb \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Avval requirements — kod o'zgarsa, paketlar qayta o'rnatilmaydi
COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip && \
    python -m pip install -r /app/requirements.txt

# Loyiha kodlari
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

WORKDIR /app/backend

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
