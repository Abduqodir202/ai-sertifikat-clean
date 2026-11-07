(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const csrf = () => {
    const item = document.cookie.split("; ").find(x => x.startsWith("csrftoken="));
    return item ? decodeURIComponent(item.split("=")[1]) : "";
  };
  const state = { mode: "practice", questions: [], startedAt: 0, timerId: null, remaining: 0, reviewed: false };

  const show = (id, yes = true) => { $(id).hidden = !yes; };
  const api = async (url, options = {}) => {
    const response = await fetch(url, {
      credentials: "same-origin",
      ...options,
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf(), ...(options.headers || {}) }
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "So‘rov bajarilmadi.");
    return data;
  };

  function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll(".mp-mode").forEach(b => b.classList.toggle("active", b.dataset.mode === mode));
    show("practiceSettings", mode === "practice");
    show("examIntro", mode === "exam");
    show("quiz", false); show("result", false);
  }
  document.querySelectorAll(".mp-mode").forEach(b => b.addEventListener("click", () => setMode(b.dataset.mode)));

  async function start(mode) {
    try {
      const params = new URLSearchParams({ mode });
      if (mode === "practice") {
        params.set("topic", $("topicSelect").value);
        params.set("level", $("levelSelect").value);
      }
      const data = await api(`/matematika/api/questions/?${params}`);
      if (!data.questions.length) throw new Error("Tanlangan mezonlar bo‘yicha savollar topilmadi.");
      state.mode = mode; state.questions = data.questions; state.startedAt = Date.now(); state.reviewed = false;
      show("practiceSettings", false); show("examIntro", false); show("result", false); show("quiz", true);
      $("timer").hidden = mode !== "exam";
      if (mode === "exam") startTimer(data.duration_seconds);
      renderQuestions();
      updateProgress();
      window.scrollTo({ top: $("quiz").offsetTop - 20, behavior: "smooth" });
    } catch (e) { alert(e.message); }
  }

  function renderQuestions() {
    const host = $("questionList"); host.innerHTML = "";
    state.questions.forEach((q, i) => {
      const card = document.createElement("article");
      card.className = "mp-question"; card.dataset.id = q.id;
      const meta = document.createElement("div"); meta.className = "mp-qmeta";
      const topic = document.createElement("span"); topic.className = "mp-tag"; topic.textContent = q.topic_label;
      const level = document.createElement("span"); level.className = "mp-tag"; level.textContent = q.level_label;
      const source = document.createElement("span"); source.className = "mp-tag";
      source.textContent = q.source === "ai" ? "AI yaratgan" : (q.source === "official_sample" ? "Rasmiy namunaga asoslangan" : "Mashq savoli");
      meta.append(topic, level, source);
      const title = document.createElement("div"); title.className = "mp-qtext"; title.textContent = `${i + 1}. ${q.text}`;
      card.append(meta, title);
      q.options.forEach((opt, j) => {
        const label = document.createElement("label"); label.className = "mp-option";
        const input = document.createElement("input"); input.type = "radio"; input.name = `q-${q.id}`; input.value = j;
        input.addEventListener("change", updateProgress);
        const text = document.createElement("span"); text.textContent = `${"ABCD"[j] || j + 1}) ${opt}`;
        label.append(input, text); card.append(label);
      });
      const explanation = document.createElement("div"); explanation.className = "mp-explanation"; explanation.dataset.explanation = "1";
      card.append(explanation); host.append(card);
    });
    $("submitQuiz").textContent = state.mode === "exam" ? "Imtihonni yakunlash" : "Javoblarni tekshirish";
  }

  function updateProgress() {
    const answered = state.questions.filter(q => document.querySelector(`input[name="q-${q.id}"]:checked`)).length;
    $("progressText").textContent = `${answered} / ${state.questions.length} javob`;
    $("progressBar").style.width = `${answered / state.questions.length * 100}%`;
  }

  function startTimer(seconds) {
    clearInterval(state.timerId); state.remaining = seconds; updateTimer();
    state.timerId = setInterval(() => {
      state.remaining--; updateTimer();
      if (state.remaining <= 0) { clearInterval(state.timerId); finish(); }
    }, 1000);
  }
  function updateTimer() {
    const m = Math.floor(state.remaining / 60), s = state.remaining % 60;
    $("timer").textContent = `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
    $("timer").classList.toggle("warning", state.remaining <= 300);
  }

  async function finish() {
    if (state.reviewed) return;
    state.reviewed = true; clearInterval(state.timerId);
    const answers = {};
    state.questions.forEach(q => {
      const selected = document.querySelector(`input[name="q-${q.id}"]:checked`);
      answers[q.id] = selected ? Number(selected.value) : null;
    });
    try {
      const data = await api("/matematika/api/submit/", {
        method: "POST",
        body: JSON.stringify({
          mode: state.mode, question_ids: state.questions.map(q => q.id), answers,
          topic: $("topicSelect").value, level: $("levelSelect").value,
          duration_seconds: Math.floor((Date.now() - state.startedAt) / 1000)
        })
      });
      showReview(data);
    } catch (e) { state.reviewed = false; alert(e.message); }
  }

  function showReview(data) {
    data.details.forEach(d => {
      const card = document.querySelector(`.mp-question[data-id="${d.id}"]`);
      if (!card) return;
      card.classList.add("review", d.is_correct ? "correct" : "wrong");
      const options = card.querySelectorAll(".mp-option");
      options.forEach((label, i) => {
        const input = label.querySelector("input"); input.disabled = true;
        if (i === d.correct_index) label.classList.add("right");
        if (d.chosen === i && !d.is_correct) label.classList.add("chosen-wrong");
      });
      const exp = card.querySelector("[data-explanation]");
      exp.textContent = `To‘g‘ri javob: ${"ABCD"[d.correct_index]}) ${d.correct_text}. ${d.explanation || ""}`;
    });
    $("score").textContent = `${data.correct} / ${data.total} · ${data.percent}%`;
    $("resultMessage").textContent = data.percent >= 80 ? "Juda yaxshi natija!" : data.percent >= 50 ? "Yaxshi urinish. Xatolarni tahlil qiling." : "Mavzularni takrorlab, yana urinib ko‘ring.";
    $("resultMeta").textContent = data.saved ? "Natija profilingizda saqlandi." : "Natijani saqlash uchun akkauntingizga kiring.";
    show("result", true);
    $("submitQuiz").disabled = true;
    window.scrollTo({ top: $("result").offsetTop - 20, behavior: "smooth" });
    loadHistory();
  }

  async function loadHistory() {
    try {
      const data = await api("/matematika/api/history/");
      if (!data.items.length) return;
      $("historyList").innerHTML = "";
      data.items.forEach(item => {
        const row = document.createElement("div"); row.className = "mp-history-row";
        const left = document.createElement("span"); left.textContent = `${item.created_at} · ${item.mode}`;
        const right = document.createElement("b"); right.textContent = `${item.correct}/${item.total} (${item.percent}%)`;
        row.append(left, right); $("historyList").append(row);
      });
      show("history", true);
    } catch (_) { /* Mehmon foydalanuvchida tarix mavjud bo'lmasligi mumkin. */ }
  }

  $("startPractice").addEventListener("click", () => start("practice"));
  $("startExam").addEventListener("click", () => start("exam"));
  $("submitQuiz").addEventListener("click", finish);
  $("cancelQuiz").addEventListener("click", () => {
    if (confirm("Joriy testdan chiqasizmi? Javoblar saqlanmaydi.")) {
      clearInterval(state.timerId); show("quiz", false); setMode(state.mode);
    }
  });
  $("again").addEventListener("click", () => {
    $("submitQuiz").disabled = false; show("result", false); show("quiz", false);
    setMode("practice"); window.scrollTo({top:0,behavior:"smooth"});
  });
  $("generateAI").addEventListener("click", async () => {
    const btn = $("generateAI"); btn.disabled = true; btn.textContent = "Savollar yaratilmoqda...";
    try {
      const data = await api("/matematika/api/ai-generate/", {
        method: "POST",
        body: JSON.stringify({ topic: $("topicSelect").value === "all" ? "algebra" : $("topicSelect").value,
          level: $("levelSelect").value === "all" ? "medium" : $("levelSelect").value, count: 5 })
      });
      alert(`${data.created} ta yangi AI savoli yaratildi. Endi mashqni qayta boshlang.`);
    } catch (e) { alert(e.message); }
    finally { btn.disabled = false; btn.textContent = "✨ AI orqali 5 ta yangi savol yaratish"; }
  });
  setMode("practice");
  loadHistory();
})();
