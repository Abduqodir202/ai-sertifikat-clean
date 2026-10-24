"use strict";

(() => {
    console.log("AI Sertifikat: rus-esse.js ishga tushdi");

    const API_URL = "/api/check-essay/";
    const OCR_URL = "/api/ocr/";
    const LOGIN_URL = "/accounts/login/";
    const REGISTER_URL = "/accounts/signup/";
    const USAGE_URL = "/api/essay-usage/";

    let essayUsage = null;
    let usageLoading = true;

    const $ = (selector) => document.querySelector(selector);
    const byId = (id) => document.getElementById(id);

    const essayText = byId("essayText");
    const essayFile = byId("essayFile");
    const essayTopic = byId("essayTopic");
    const studentName = byId("studentName");

    const wordCount = byId("wordCount");
    const charCount = byId("charCount");
    const paragraphCount = byId("paragraphCount");
    const wordStatus = byId("wordStatus");
    const ocrStatus = byId("ocrStatus");
    const imagePreviewList = byId("imagePreviewList");
    const clearImagesBtn = byId("clearImagesBtn");

    let selectedImages = [];
    let imagePreviewUrls = [];

    const result = byId("result");
    const totalScore = byId("totalScore");
    const reviewText = byId("reviewText");

    let checking = false;
    let authModalVisible = false;

    const CRITERIA = [
        { name: "Раскрытие темы", max: 20 },
        { name: "Аргументация и примеры", max: 15 },
        { name: "Структура и логика", max: 10 },
        { name: "Лексика и стилистика", max: 10 },
        { name: "Грамотность", max: 10 },
        { name: "Оригинальность", max: 10 }
    ];

    const MAX_TOTAL = 75;

    // ==================================================
    // YORDAMCHI FUNKSIYALAR
    // ==================================================

    function setText(element, value) {
        if (element) {
            element.textContent = value;
        }
    }

    function getFirstValue(object, keys) {
        for (const key of keys) {
            if (
                object &&
                object[key] !== undefined &&
                object[key] !== null
            ) {
                return object[key];
            }
        }

        return undefined;
    }

    function getCookie(name) {
        const cookies = document.cookie
            ? document.cookie.split(";")
            : [];

        for (const cookie of cookies) {
            const item = cookie.trim();

            if (item.startsWith(name + "=")) {
                return decodeURIComponent(
                    item.substring(name.length + 1)
                );
            }
        }

        return "";
    }

    // ==================================================
    // KUNLIK BEPUL ESSE LIMITI
    // ==================================================

    function renderEssayUsage(usage) {
        essayUsage = usage;

        let box = byId("essayUsageBox");

        if (!box) {
            box = document.createElement("section");
            box.id = "essayUsageBox";

            box.style.cssText = `
                margin: 18px 0;
                padding: 18px;
                border: 1px solid #cbd5e1;
                border-radius: 14px;
                background: #f0f7ff;
                color: #1e293b;
                font-family: Arial, sans-serif;
            `;

            const anchor = essayText
                ? essayText.closest("form") || essayText.parentElement
                : null;

            if (anchor && anchor.parentElement) {
                anchor.parentElement.insertBefore(box, anchor);
            } else {
                document.body.prepend(box);
            }
        }

        box.replaceChildren();

                if (usage.unlimited) {
            box.innerHTML = `
                <strong>♾️ Безлимитный доступ активен</strong>
                <p>У вас нет дневных ограничений на проверку эссе.</p>
            `;
            return;
        }

        const limit = Number(usage.daily_limit ?? 5);
        const used = Number(usage.used_today ?? 0);

        const remaining = Math.max(
            0,
            Number(usage.remaining ?? limit - used)
        );

        const percent = limit > 0
            ? Math.min(100, Math.max(0, (used / limit) * 100))
            : 0;

        box.innerHTML = `
            <strong>🎁  Ежедневная бесплатная проверка эссе </strong>
            <p>Ваш дневной лимит: ${limit} эссе</p>

            <div style="
                height: 8px;
                background: #dbeafe;
                border-radius: 10px;
                overflow: hidden;
            ">
                <div style="
                    width: ${percent}%;
                    height: 100%;
                    background: #16a34a;
                    border-radius: 10px;
                "></div>
            </div>

            <p><strong>Осталось проверок: ${remaining}</strong></p>


            <small>
                Лимит обновляется каждый день.
                Неиспользованные проверки на следующий день не переносятся.
            </small>
        `;

        if (remaining === 0) {
            const message = document.createElement("div");

            message.style.cssText = `
                margin-top: 14px;
                padding-top: 12px;
                border-top: 1px solid #cbd5e1;
            `;

            message.innerHTML = `
                <strong>Сегодня ваш бесплатный лимит исчерпан.</strong>
                <p>
                    Чтобы продолжить проверку эссе, ознакомьтесь с тарифом Unlimited.
                </p>
                <p><strong>30 дней — 600 000 сумов</strong></p>
            `;

            const button = document.createElement("button");
            button.type = "button";
            button.textContent = "Посмотреть тариф";

            button.style.cssText = `
                padding: 10px 16px;
                border: 0;
                border-radius: 8px;
                background: #2563eb;
                color: white;
                cursor: pointer;
            `;

            button.addEventListener("click", () => {
    const tariffsUrl = byId("tariffs-config")?.dataset.url;

    if (tariffsUrl) {
        window.location.href = tariffsUrl;
    } else {
        console.error(
            "Не удалось найти ссылку на страницу тарифов."
        );
    }
});



            message.appendChild(button);
            box.appendChild(message);
        }
    }
async function refreshEssayUsage() {
    usageLoading = true;

    const box = document.getElementById("essayUsageBox");

    if (box) {
        box.innerHTML = `
            <h3>📊 Ежедневные проверки</h3>
            <p>Загрузка информации о проверках...</p>
        `;
    }

    try {
        const response = await fetch(USAGE_URL, {
            method: "GET",
            headers: {
                "Accept": "application/json"
            },
            credentials: "same-origin"
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                data.detail ||
                `Ошибка сервера: ${response.status}`
            );
        }

        renderEssayUsage(data);

    } catch (error) {
        console.error("Essay usage error:", error);

        if (box) {
            box.innerHTML = `
                <h3>📊 Ежедневные проверки</h3>
                <p>Не удалось загрузить информацию о проверках.</p>
                <p>Пожалуйста, попробуйте ещё раз.</p>
                <button
                    type="button"
                    id="retryEssayUsage"
                    class="essay-usage-cta"
                >
                    Повторить
                </button>
            `;

            const retryButton = document.getElementById("retryEssayUsage");

            if (retryButton) {
                retryButton.addEventListener("click", refreshEssayUsage);
            }
        }
    } finally {
        usageLoading = false;
    }
}

    function getStatistics(text) {
        const trimmed = text.trim();

        const words = trimmed
            ? trimmed.split(/\s+/).filter(Boolean)
            : [];

        const paragraphs = trimmed
            ? trimmed.split(/\n\s*\n/).filter(
                paragraph => paragraph.trim()
            )
            : [];

        return {
            words: words.length,
            characters: text.length,
            paragraphs: paragraphs.length
        };
    }

    function updateEssayText(text) {
        if (!essayText) return;

        essayText.value = text;

        essayText.dispatchEvent(
            new Event("input", { bubbles: true })
        );

        analyzeText();
    }

    // ==================================================
    // RO'YXATDAN O'TISH OYNASI
    // ==================================================

    function showAuthRequiredModal() {
        if (authModalVisible) return;

        const existing = byId("authRequiredModal");

        if (existing) {
            existing.style.display = "flex";
            authModalVisible = true;
            return;
        }

        authModalVisible = true;

        const currentUrl =
            window.location.pathname + window.location.search;

        const next = encodeURIComponent(currentUrl);

        const registerUrl = `${REGISTER_URL}?next=${next}`;
        const loginUrl = `${LOGIN_URL}?next=${next}`;

        const modal = document.createElement("div");
        modal.id = "authRequiredModal";

        modal.style.cssText = `
            position: fixed;
            inset: 0;
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            background: rgba(15, 23, 42, 0.68);
            backdrop-filter: blur(5px);
            box-sizing: border-box;
        `;

        const card = document.createElement("div");

        card.style.cssText = `
            position: relative;
            width: 100%;
            max-width: 430px;
            padding: 32px 25px;
            background: #ffffff;
            border-radius: 22px;
            text-align: center;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.25);
            box-sizing: border-box;
            font-family: Arial, sans-serif;
        `;

        const closeTop = document.createElement("button");
        closeTop.type = "button";
        closeTop.setAttribute("aria-label", "Yopish");
        closeTop.textContent = "×";

        closeTop.style.cssText = `
            position: absolute;
            top: 10px;
            right: 15px;
            border: none;
            background: transparent;
            color: #94a3b8;
            font-size: 30px;
            cursor: pointer;
        `;

        const icon = document.createElement("div");
        icon.textContent = "🔐";
        icon.style.fontSize = "48px";
        icon.style.marginBottom = "14px";

        const heading = document.createElement("h2");
        heading.textContent = "Avval ro‘yxatdan o‘ting!";
        heading.style.cssText = `
            color: #24345b;
            font-size: 23px;
            line-height: 1.35;
            margin: 0 0 12px;
        `;

        const description = document.createElement("p");
        description.textContent =
            "Esseni tekshirish uchun avval ro‘yxatdan o‘ting " +
            "yoki hisobingizga kiring.";

        description.style.cssText = `
            color: #64748b;
            font-size: 15px;
            line-height: 1.7;
            margin: 0 0 24px;
        `;

        const registerLink = document.createElement("a");
        registerLink.href = registerUrl;
        registerLink.textContent = "Ro‘yxatdan o‘tish";

        registerLink.style.cssText = `
            display: block;
            padding: 15px 18px;
            border-radius: 12px;
            color: #ffffff;
            background: linear-gradient(90deg, #3978f6, #9850f5);
            text-decoration: none;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 12px;
            box-sizing: border-box;
        `;

        const loginLink = document.createElement("a");
        loginLink.href = loginUrl;
        loginLink.textContent = "Tizimga kirish";

        loginLink.style.cssText = `
            display: block;
            padding: 15px 18px;
            border-radius: 12px;
            color: #4f46e5;
            background: #eef2ff;
            text-decoration: none;
            font-size: 15px;
            font-weight: 700;
            box-sizing: border-box;
        `;

        const closeButton = document.createElement("button");
        closeButton.type = "button";
        closeButton.textContent = "Yopish";

        closeButton.style.cssText = `
            margin-top: 19px;
            padding: 8px 18px;
            border: none;
            background: transparent;
            color: #64748b;
            font-size: 14px;
            cursor: pointer;
        `;

        function closeModal() {
            modal.remove();
            authModalVisible = false;
            document.removeEventListener("keydown", handleEscape);
        }

        closeTop.addEventListener("click", closeModal);
        closeButton.addEventListener("click", closeModal);

        modal.addEventListener("click", (event) => {
            if (event.target === modal) {
                closeModal();
            }
        });

        function handleEscape(event) {
            if (event.key === "Escape" && byId("authRequiredModal")) {
                closeModal();
            }
        }

        document.addEventListener("keydown", handleEscape);

        card.append(
            closeTop,
            icon,
            heading,
            description,
            registerLink,
            loginLink,
            closeButton
        );

        modal.appendChild(card);
        document.body.appendChild(modal);
    }

    // ==================================================
    // MATN STATISTIKASI
    // ==================================================

    function analyzeText() {
        if (!essayText) return;

        const stats = getStatistics(essayText.value);

        setText(wordCount, stats.words);
        setText(charCount, stats.characters);
        setText(paragraphCount, stats.paragraphs);

        if (!wordStatus) return;

        wordStatus.className = "word-status";

        if (stats.words === 0) {
            wordStatus.classList.add("neutral");
            wordStatus.textContent =
                "Введите эссе для проверки объёма.";
        } else if (stats.words < 100) {
            wordStatus.classList.add("warning");
            wordStatus.textContent =
                "⚠️ Менее 100 слов. Проверьте требования к объёму.";
        } else {
            wordStatus.classList.add("success");
            wordStatus.textContent =
                "✓ Объём текста позволяет выполнить проверку.";
        }
    }

    // ==================================================
    // NATIJA VA DARAJA
    // ==================================================

    function displayOfficialResult(score75, backendLevel = "") {
        const score = Number(score75);

        const validScore =
            score75 !== null &&
            score75 !== undefined &&
            score75 !== "" &&
            Number.isFinite(score) &&
            score >= 0 &&
            score <= MAX_TOTAL;

        setText(
            totalScore,
            validScore ? Number(score.toFixed(2)) : "—"
        );

        let levelElement = byId("scoreLevel");

        if (!levelElement && result) {
            levelElement = document.createElement("div");
            levelElement.id = "scoreLevel";
            levelElement.className = "score-level";

            const scoreContainer = result.querySelector(".result-score");

            if (scoreContainer) {
                scoreContainer.insertAdjacentElement(
                    "afterend",
                    levelElement
                );
            }
        }

        if (!levelElement) return;

        let level = "Daraja belgilanmagan";

        if (validScore) {
            if (backendLevel) {
                level = String(backendLevel);
            } else if (score >= 70) {
                level = "A+";
            } else if (score >= 65) {
                level = "A";
            } else if (score >= 60) {
                level = "B+";
            } else if (score >= 55) {
                level = "B";
            } else if (score >= 50) {
                level = "C+";
            } else if (score >= 46) {
                level = "C";
            }
        }

        levelElement.textContent = "Daraja: " + level;
    }

    function showResult() {
        if (!result) {
            console.error("HTML element #result topilmadi.");
            return;
        }

        result.classList.add("show");

        result.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    function showMessage(message) {
        if (reviewText) {
            reviewText.textContent = message;
            showResult();
        } else {
            alert(message);
        }
    }

    function resetResult() {
        setText(totalScore, "—");
        setText(reviewText, "");

        displayOfficialResult(null);

        [
            "criteriaResult",
            "errorsList",
            "recommendationsList",
            "highlightedEssay"
        ].forEach(id => {
            const element = byId(id);
            if (element) element.replaceChildren();
        });
    }

    // ==================================================
    // BAHOLASH MEZONLARI
    // ==================================================

    function displayCriteria(criteria) {
        let container = byId("criteriaResult");

        if (!container && result) {
            container = document.createElement("div");
            container.id = "criteriaResult";
            container.className = "criteria-results";
            result.appendChild(container);
        }

        if (!container) return;

        container.replaceChildren();

        const heading = document.createElement("h3");
        heading.textContent = "📊 Критерии оценки";
        container.appendChild(heading);

        if (!Array.isArray(criteria) || criteria.length === 0) {
            const message = document.createElement("p");
            message.textContent =
                "Сервер не вернул оценки по критериям.";
            container.appendChild(message);
            return;
        }

        let earnedTotal = 0;
        let maximumTotal = 0;
        let scoredCount = 0;

        CRITERIA.forEach((definition, index) => {
            const criterion = criteria[index] || {};

            const name =
                criterion.name ||
                criterion.title ||
                criterion.criterion ||
                definition.name;

            const rawScore = getFirstValue(criterion, [
                "score",
                "points",
                "value",
                "балл"
            ]);

            const rawMax = getFirstValue(criterion, [
                "max_score",
                "maxScore",
                "maximum",
                "max"
            ]);

            const maxScore = Number(rawMax ?? definition.max);
            const score = Number(rawScore);

            const validScore =
                rawScore !== undefined &&
                rawScore !== null &&
                rawScore !== "" &&
                Number.isFinite(score) &&
                Number.isFinite(maxScore) &&
                maxScore > 0 &&
                score >= 0 &&
                score <= maxScore;

            const row = document.createElement("div");
            row.className = "result-item";

            const label = document.createElement("span");
            label.className = "criterion-name";
            label.textContent = `${index + 1}. ${name}`;

            const scoreElement = document.createElement("strong");
            scoreElement.className = "criterion-score";
            scoreElement.textContent = validScore
                ? `${score} / ${maxScore}`
                : `— / ${maxScore}`;

            row.append(label, scoreElement);
            container.appendChild(row);

            const reason = document.createElement("p");
            reason.className = "criterion-reason";
            reason.textContent =
                getFirstValue(criterion, [
                    "reason",
                    "comment",
                    "feedback",
                    "explanation",
                    "description"
                ]) || "Комментарий отсутствует.";

            container.appendChild(reason);

            if (validScore) {
                earnedTotal += score;
                maximumTotal += maxScore;
                scoredCount++;
            }
        });

        const summary = document.createElement("div");
        summary.className = "criteria-summary";

        summary.textContent =
            scoredCount === CRITERIA.length
                ? `Сумма баллов: ${earnedTotal} / ${maximumTotal}`
                : `Получены оценки по ${scoredCount} из ${CRITERIA.length} критериев.`;

        container.appendChild(summary);
    }

    // ==================================================
    // XATOLARNI MATNDA BELGILASH
    // ==================================================

    function highlightEssay(container, essay, errors) {
        container.replaceChildren();

        const fragments = errors
            .filter(error =>
                error &&
                typeof error === "object" &&
                error.fragment
            )
            .map(error => ({
                fragment: String(error.fragment),
                correction: String(error.correction || ""),
                explanation: String(error.explanation || "")
            }))
            .sort((a, b) =>
                b.fragment.length - a.fragment.length
            );

        let position = 0;

        while (position < essay.length) {
            let found = null;
            let foundAt = -1;

            for (const error of fragments) {
                const index = essay.indexOf(
                    error.fragment,
                    position
                );

                if (
                    index !== -1 &&
                    (foundAt === -1 || index < foundAt)
                ) {
                    foundAt = index;
                    found = error;
                }
            }

            if (!found || foundAt === -1) {
                container.appendChild(
                    document.createTextNode(essay.slice(position))
                );
                break;
            }

            if (foundAt > position) {
                container.appendChild(
                    document.createTextNode(
                        essay.slice(position, foundAt)
                    )
                );
            }

            const span = document.createElement("span");
            span.className = "essay-error";
            span.textContent = found.fragment;

            span.title = found.correction
                ? `Исправление: ${found.correction}`
                : found.explanation || "Ошибка";

            container.appendChild(span);

            position = foundAt + found.fragment.length;
        }

        if (!essay.length) {
            container.textContent = essay;
        }
    }

    // ==================================================
    // XATOLAR RO'YXATI
    // ==================================================

    function displayErrors(errors) {
        const container = byId("errorsList");
        const highlightedEssay = byId("highlightedEssay");

        if (container) {
            container.replaceChildren();
        }

        if (highlightedEssay && essayText) {
            highlightEssay(
                highlightedEssay,
                essayText.value.trim(),
                Array.isArray(errors) ? errors : []
            );
        }

        if (!container) return;

        if (!Array.isArray(errors) || errors.length === 0) {
            const message = document.createElement("p");
            message.textContent = "Ошибок не найдено.";
            container.appendChild(message);
            return;
        }

        errors.forEach((error, index) => {
            const item = document.createElement("div");
            item.className = "error-item";

            if (typeof error === "string") {
                item.textContent = `${index + 1}. ${error}`;
                container.appendChild(item);
                return;
            }

            const type = document.createElement("div");
            type.className = "error-type";
            type.textContent =
                `${index + 1}. ${error.type || "Языковая ошибка"}`;

            item.appendChild(type);

            if (error.fragment) {
                const fragment = document.createElement("div");
                fragment.className = "error-fragment";
                fragment.textContent = `❌ ${error.fragment}`;
                item.appendChild(fragment);
            }

            if (error.correction) {
                const correction = document.createElement("div");
                correction.className = "error-correction";
                correction.textContent = `✅ ${error.correction}`;
                item.appendChild(correction);
            }

            if (error.explanation) {
                const explanation = document.createElement("div");
                explanation.className = "error-explanation";
                explanation.textContent = error.explanation;
                item.appendChild(explanation);
            }

            container.appendChild(item);
        });
    }

    // ==================================================
    // TAVSIYALAR
    // ==================================================

    function displayRecommendations(recommendations) {
        const container = byId("recommendationsList");
        if (!container) return;

        container.replaceChildren();

        if (
            !Array.isArray(recommendations) ||
            recommendations.length === 0
        ) {
            const message = document.createElement("p");
            message.textContent = "Рекомендаций нет.";
            container.appendChild(message);
            return;
        }

        recommendations.forEach((recommendation, index) => {
            const item = document.createElement("div");
            item.className = "recommendation-item";

            const text = typeof recommendation === "string"
                ? recommendation
                : (
                    recommendation.text ||
                    recommendation.recommendation ||
                    recommendation.description ||
                    JSON.stringify(recommendation)
                );

            item.textContent = `${index + 1}. ${text}`;
            container.appendChild(item);
        });
    }

    // ==================================================
    // API NATIJASINI KO'RSATISH
    // ==================================================

    function displayResult(data) {
        if (!data || typeof data !== "object") {
            throw new Error("Сервер вернул некорректный ответ.");
        }

        console.log("AI RESULT:", data);

        const scoreValue = getFirstValue(data, [
            "total_score",
            "totalScore",
            "score_75",
            "final_score",
            "score",
            "overall_score"
        ]);

        if (
            scoreValue !== undefined &&
            scoreValue !== null &&
            scoreValue !== ""
        ) {
            const score = Number(scoreValue);

            if (
                !Number.isFinite(score) ||
                score < 0 ||
                score > MAX_TOTAL
            ) {
                throw new Error(
                    "Балл должен быть в диапазоне от 0 до 75."
                );
            }

            displayOfficialResult(
                score,
                data.level ||
                data.grade ||
                data.result_level ||
                ""
            );
        } else {
            displayOfficialResult(null);
        }

        if (reviewText) {
            reviewText.textContent =
                data.review ||
                data.feedback ||
                data.overall_review ||
                data.recommendation_text ||
                "Обзор отсутствует.";
        }

        displayCriteria(getFirstValue(data, [
            "criteria",
            "criteria_scores",
            "rubric",
            "assessment_criteria"
        ]));

        displayErrors(getFirstValue(data, [
            "errors",
            "mistakes",
            "language_errors"
        ]));

        displayRecommendations(getFirstValue(data, [
            "recommendations",
            "advice",
            "suggestions"
        ]));

        const originalEssay = byId("originalEssay");

        if (originalEssay && essayText) {
            originalEssay.textContent = essayText.value.trim();
        }
    }

    // ==================================================
    // API JAVOBI VA AUTENTIFIKATSIYA
    // ==================================================

    async function readApiResponse(response) {
        const raw = await response.text();

        let data = {};

        try {
            data = raw ? JSON.parse(raw) : {};
        } catch {
            data = {};
        }

        const detail = String(
            data.detail || data.error || data.message || raw || ""
        );

        const authenticationRequired =
            response.status === 401 ||
            (
                response.status === 403 &&
                /authentication credentials were not provided|not authenticated|avval tizimga kiring/i.test(
                    detail
                )
            );

        if (authenticationRequired) {
            showAuthRequiredModal();
            return null;
        }

        if (!response.ok) {
            const error = new Error(
                `Ошибка сервера (${response.status}): ${
                    data.detail || data.error || data.message || raw
                }`
            );

            error.status = response.status;
            error.data = data;

            throw error;
        }

        return data;
    }

    // ==================================================
    // ASOSIY ESSE TEKSHIRISH
    // ==================================================

    async function checkEssay() {
        if (checking) return;

        if (usageLoading) {
            alert("Kunlik limit tekshirilmoqda. Biroz kuting.");
            return;
        }

        if (
            essayUsage &&
            !essayUsage.unlimited &&
            Number(essayUsage.remaining) <= 0
        ) {
            renderEssayUsage(essayUsage);
            return;
        }

        if (!essayText) {
            alert("Esse matni maydoni topilmadi.");
            return;
        }

        if (
            !essayText.value.trim() &&
            selectedImages.length === 0
        ) {
            alert("Esse matnini kiriting yoki 1–5 ta rasm yuklang.");
            return;
        }

        const button = $(".check-btn");

        const originalText = button
            ? button.textContent
            : "Проверить эссе";

        checking = true;

        if (button) {
            button.disabled = true;
            button.textContent = "⏳ Rasmlar tayyorlanmoqda...";
        }

        try {
            let text = essayText.value.trim();

            let topic = essayTopic
                ? essayTopic.value.trim()
                : "";

            // 1. Avval rasmlardan matn olish
            if (selectedImages.length > 0) {
                const imageResult = await extractTextFromImages();

                if (imageResult === null) return;

                const extractedEssay = String(
                    imageResult.essay || ""
                ).trim();

                if (!extractedEssay) {
                    throw new Error(
                        "Rasmdan matn olinmadi. Boshqa rasmni sinab ko‘ring."
                    );
                }

                text = text
                    ? `${text}\n\n${extractedEssay}`
                    : extractedEssay;

                updateEssayText(text);

                if (imageResult.topic && essayTopic) {
                    essayTopic.value = imageResult.topic;
                }

                topic = essayTopic
                    ? essayTopic.value.trim()
                    : String(imageResult.topic || "").trim();

                if (ocrStatus) {
                    ocrStatus.textContent =
                        "✅ Matn olindi. Mavzuni tekshirib, davom eting.";
                }
            }

            if (!text.trim()) {
                throw new Error("Esse matni bo‘sh.");
            }

            if (text.length > 20000) {
                throw new Error(
                    "Esse matni 20 000 belgidan oshmasligi kerak."
                );
            }

            if (!topic) {
                if (essayTopic) {
                    essayTopic.focus();
                }

                throw new Error(
                    "OCR matni olindi. Endi «ТЕМА ЭССЕ» maydoniga " +
                    "esse mavzusini kiriting va yana tekshirish tugmasini bosing."
                );
            }

            const stats = getStatistics(text);

            if (button) {
                button.textContent = "⏳ Esse tekshirilmoqda...";
            }

            const requestData = {
                essay: text,
                topic: topic,
                student_name: studentName
                    ? studentName.value.trim()
                    : "",
                subject: "russian",
                language: "ru",
                word_count: stats.words,
                character_count: stats.characters,
                paragraph_count: stats.paragraphs
            };

            const headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            };

            const csrfToken = getCookie("csrftoken");

            if (csrfToken) {
                headers["X-CSRFToken"] = csrfToken;
            }

            const response = await fetch(API_URL, {
                method: "POST",
                headers,
                credentials: "same-origin",
                body: JSON.stringify(requestData)
            });

            const data = await readApiResponse(response);

            if (data === null) return;

            const resultData =
                data.result && typeof data.result === "object"
                    ? data.result
                    : data;

            displayResult(resultData);
            showResult();

            // Backend usage ma'lumotini qaytarsa, darhol ko'rsatamiz.
            if (data.usage) {
                renderEssayUsage(data.usage);
            } else if (resultData.usage) {
                renderEssayUsage(resultData.usage);
            } else {
                await refreshEssayUsage();
            }

            if (ocrStatus && selectedImages.length > 0) {
                ocrStatus.textContent =
                    "✅ Rasmlardagi esse tekshirildi.";
            }

        } catch (error) {
            console.error("Essay check error:", error);

            // Kunlik limit tugagan bo'lsa, ekrandagi ma'lumotni yangilaymiz.
            if (error && error.status === 429) {
                const errorData = error.data || {};

                if (errorData.remaining !== undefined) {
                    renderEssayUsage({
                        unlimited: false,
                        daily_limit: errorData.daily_limit ?? 5,
                        used_today: errorData.used_today ?? 5,
                        remaining: errorData.remaining
                    });
                } else {
                    await refreshEssayUsage();
                }
            }

            showMessage(
                "Esseni tekshirishda xato: " + error.message
            );

        } finally {
            checking = false;

            if (button) {
                button.disabled = false;
                button.textContent = originalText;
            }
        }
    }

    // HTML onclick va boshqa skriptlar uchun
    window.checkEssay = checkEssay;
    window.displayOfficialResult = displayOfficialResult;
    window.showAuthRequiredModal = showAuthRequiredModal;


    // ==================================================
    // KO'P RASM TANLASH VA PREVIEW
    // ==================================================

    function updateImageInput() {
        if (!essayFile) return;

        const transfer = new DataTransfer();

        selectedImages.forEach(file => {
            transfer.items.add(file);
        });

        essayFile.files = transfer.files;

        if (clearImagesBtn) {
            clearImagesBtn.style.display =
                selectedImages.length ? "inline-block" : "none";
        }

        if (ocrStatus) {
            ocrStatus.textContent = selectedImages.length
                ? `${selectedImages.length}/5 ta rasm tanlandi. Tekshirish uchun tugmani bosing.`
                : "1–5 ta rasm tanlashingiz mumkin.";
        }
    }

    function renderImagePreviews() {
        if (!imagePreviewList) return;

        imagePreviewUrls.forEach(url => URL.revokeObjectURL(url));
        imagePreviewUrls = [];

        imagePreviewList.replaceChildren();

        selectedImages.forEach((file, index) => {
            const card = document.createElement("div");
            card.className = "image-preview-item";

            const image = document.createElement("img");
            image.alt = `Esse rasmi ${index + 1}`;
            image.src = URL.createObjectURL(file);

            imagePreviewUrls.push(image.src);

            image.style.cssText = `
                display: block;
                width: 100%;
                max-width: 150px;
                height: 150px;
                object-fit: contain;
                border-radius: 10px;
                background: #f1f5f9;
            `;

            const name = document.createElement("small");
            name.textContent = `${index + 1}. ${file.name}`;

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.textContent = "O‘chirish";
            removeButton.setAttribute(
                "aria-label",
                `${index + 1}-rasmni o‘chirish`
            );

            removeButton.addEventListener("click", () => {
                selectedImages.splice(index, 1);
                renderImagePreviews();
                updateImageInput();
            });

            card.style.cssText = `
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
                padding: 10px;
                border: 1px solid #dbe4f0;
                border-radius: 12px;
                min-width: 0;
            `;

            removeButton.style.cssText = `
                border: none;
                border-radius: 8px;
                padding: 7px 10px;
                background: #fee2e2;
                color: #b91c1c;
                cursor: pointer;
            `;

            card.append(image, name, removeButton);
            imagePreviewList.appendChild(card);
        });

        imagePreviewList.style.cssText = `
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-top: 14px;
        `;
    }

    // ==================================================
    // RASM TANLASH HODISALARI
    // ==================================================

    if (essayFile) {
        essayFile.addEventListener("change", function () {
            const files = Array.from(this.files || []);

            const allowedTypes = [
                "image/jpeg",
                "image/png",
                "image/webp"
            ];

            if (selectedImages.length + files.length > 5) {
                alert("Ko‘pi bilan 5 ta rasm tanlashingiz mumkin.");
                this.value = "";
                return;
            }

            for (const file of files) {
                if (!allowedTypes.includes(file.type)) {
                    alert(
                        `"${file.name}" qo‘llab-quvvatlanmaydi. ` +
                        "JPG, PNG yoki WEBP formatidan foydalaning."
                    );

                    this.value = "";
                    return;
                }

                if (file.size > 10 * 1024 * 1024) {
                    alert(
                        `"${file.name}" hajmi 10 MB dan katta.`
                    );

                    this.value = "";
                    return;
                }
            }

            selectedImages.push(...files);

            renderImagePreviews();
            updateImageInput();
        });
    }

    if (clearImagesBtn) {
        clearImagesBtn.addEventListener("click", () => {
            selectedImages = [];

            if (essayFile) {
                essayFile.value = "";
            }

            renderImagePreviews();
            updateImageInput();
        });
    }

    // ==================================================
    // PYTESSERACT OCR API
    // ==================================================

    async function extractTextFromImages() {
        const extractedTexts = [];
        let detectedTopic = "";

        for (
            let index = 0;
            index < selectedImages.length;
            index++
        ) {
            const file = selectedImages[index];

            if (ocrStatus) {
                ocrStatus.textContent =
                    `⏳ ${index + 1}/${selectedImages.length} ` +
                    "rasm o‘qilmoqda...";
            }

            const formData = new FormData();
            formData.append("file", file);

            const headers = {};
            const csrfToken = getCookie("csrftoken");

            if (csrfToken) {
                headers["X-CSRFToken"] = csrfToken;
            }

            let response;

            try {
                response = await fetch(OCR_URL, {
                    method: "POST",
                    headers,
                    credentials: "same-origin",
                    body: formData
                });
            } catch (error) {
                console.error("OCR tarmoq xatosi:", error);

                throw new Error(
                    "OCR serveriga ulanib bo‘lmadi. " +
                    "Internet va Django serverini tekshiring."
                );
            }

            const data = await readApiResponse(response);

            if (data === null) {
                return null;
            }

            console.log(
                `OCR API javobi (${index + 1}-rasm):`,
                data
            );

            const topic = String(data.topic || "").trim();

            const essay = String(
                data.essay || data.text || ""
            ).trim();

            if (index === 0 && topic) {
                detectedTopic = topic;
            }

            if (!essay) {
                throw new Error(
                    `${index + 1}-rasmdan matn topilmadi. ` +
                    "Django terminalidagi OCR natijasini tekshiring."
                );
            }

            extractedTexts.push(essay);

            // Har bir rasm o‘qilgandan keyin matnni ko‘rsatish.
            const currentText = extractedTexts.join("\n\n");

            updateEssayText(currentText);

            if (index === 0 && topic && essayTopic) {
                essayTopic.value = topic;

                essayTopic.dispatchEvent(
                    new Event("input", { bubbles: true })
                );
            }

            console.log(
                `OCR ${index + 1}-rasm matni:`,
                essay
            );
        }

        if (!detectedTopic && essayTopic) {
            detectedTopic = essayTopic.value.trim();
        }

        return {
            topic: detectedTopic,
            essay: extractedTexts.join("\n\n")
        };
    }

    // ==================================================
    // HODISALAR VA FAYLNI YAKUNLASH
    // ==================================================

    refreshEssayUsage();
    analyzeText();

    if (essayText) {
        essayText.addEventListener("input", analyzeText);
    }

    const checkButton = $(".check-btn");

    if (checkButton) {
        checkButton.addEventListener("click", function (event) {
            event.preventDefault();
            checkEssay();
        });
    } else {
        console.warn("Кнопка .check-btn не найдена.");
    }

    analyzeText();
})();

