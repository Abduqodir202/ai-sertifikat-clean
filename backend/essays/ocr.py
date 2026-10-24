
import io

import pytesseract
from PIL import Image, ImageOps, ImageEnhance, ImageFilter


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def image_to_text(image_bytes):
    """Rasmdagi ruscha matnni satrma-satr OCR qilish."""

    with Image.open(io.BytesIO(image_bytes)) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")

    # Kulrang rasm va kontrastni yaxshilash
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)
    gray = ImageEnhance.Contrast(gray).enhance(1.4)
    gray = gray.filter(ImageFilter.SHARPEN)

    # Rasmni 2 baravar kattalashtirish
    width, height = gray.size
    gray = gray.resize(
        (width * 2, height * 2),
        Image.Resampling.LANCZOS,
    )

    # Tesseract yordamida so'z va satrlar joylashuvini olish
    data = pytesseract.image_to_data(
        gray,
        lang="rus",
        config="--oem 3 --psm 11",
        output_type=pytesseract.Output.DICT,
    )

    lines = {}

    for i, word in enumerate(data["text"]):
        word = word.strip()

        if not word:
            continue

        key = (
            data["block_num"][i],
            data["par_num"][i],
            data["line_num"][i],
        )

        lines.setdefault(key, []).append(
            (
                data["left"][i],
                word,
            )
        )

    result = []

    for words in lines.values():
        words.sort(key=lambda item: item[0])
        line = " ".join(word for _, word in words)
        result.append(line)

    text = "\n".join(result).strip()

    print("SATRMA-SATR OCR NATIJASI:", flush=True)
    print(text, flush=True)

    return text
def file_to_text(file):
    """Yuklangan rasm yoki PDF faylni matnga aylantiradi."""

    filename = file.name.lower()
    file_bytes = file.read()

    if filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return image_to_text(file_bytes)

    if filename.endswith(".pdf"):
        return pdf_to_text(file_bytes)

    raise ValueError(
        "Faqat JPG, JPEG, PNG, WEBP yoki PDF fayl yuborish mumkin."
    )