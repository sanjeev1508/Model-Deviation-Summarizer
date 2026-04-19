/* ═══════════════════════════════════════════════════════════
   Model Deviation Summarizer · Extension Popup Script
   Onboarding Wizard + Main App  ·  v3.0
═══════════════════════════════════════════════════════════ */

/* ── Storage keys ──────────────────────────────────────────── */
const SK = {
  groqApiKey: "groqApiKey",
  groqModel:  "groqModel",
  domain:     "domain",
  language:   "language",
  onboarded:  "onboarded",
};

/* ── Helpers ───────────────────────────────────────────────── */
function store(obj) {
  return new Promise((res) => chrome.storage.local.set(obj, res));
}

function load(...keys) {
  return new Promise((res) =>
    chrome.storage.local.get(keys, (data) => res(data))
  );
}

function setBadge(id, message, type) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = message;
  el.className = type; // "success" | "error" | "info"
  el.parentElement.style.display = "block";
}

/* ── Step transitions ──────────────────────────────────────── */
let currentStep = 1;

function goToStep(next) {
  const current = document.getElementById(`step${currentStep}`);
  const target  = document.getElementById(`step${next}`);
  if (!current || !target) return;

  // Exit current
  current.classList.remove("active");
  current.classList.add("exit-left");
  setTimeout(() => {
    current.classList.remove("exit-left");
    current.style.display = "none";
  }, 320);

  // Enter next
  setTimeout(() => {
    target.style.display   = "flex";
    target.classList.add("active");
  }, 80);

  currentStep = next;
  updateDots(next);
}

function updateDots(step) {
  document.querySelectorAll(".dot").forEach((dot) => {
    const n = parseInt(dot.dataset.step);
    dot.classList.toggle("active", n === step);
    dot.classList.toggle("done", n < step);
  });
}

/* ── Eye toggle ────────────────────────────────────────────── */
document.getElementById("toggleKey").addEventListener("click", () => {
  const input = document.getElementById("groqApiKey");
  const isPass = input.type === "password";
  input.type = isPass ? "text" : "password";

  const svg = document.getElementById("eyeIcon");
  svg.innerHTML = isPass
    ? `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
       <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
       <line x1="1" y1="1" x2="23" y2="23"/>`
    : `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>`;
});

/* ── STEP 1 · Test Groq & advance ──────────────────────────── */
document.getElementById("testAndNext1").addEventListener("click", async () => {
  const btn    = document.getElementById("testAndNext1");
  const apiKey = document.getElementById("groqApiKey").value.trim();

  if (!apiKey) {
    document.getElementById("step1ConnRow").style.display = "block";
    setBadge("step1ConnBadge", "Please enter your Groq API key.", "error");
    return;
  }

  btn.disabled    = true;
  btn.textContent = "Testing connection…";

  try {
    const res  = await fetch("http://127.0.0.1:8000/test-groq", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ api_key: apiKey }),
    });
    const data = await res.json();

    if (data.ok) {
      await store({ [SK.groqApiKey]: apiKey });
      document.getElementById("step1ConnRow").style.display = "block";
      setBadge("step1ConnBadge", `Connected · Model: ${data.model}`, "success");
      setTimeout(() => goToStep(2), 700);
    } else {
      setBadge("step1ConnBadge", data.error || "Connection failed. Check your key.", "error");
      document.getElementById("step1ConnRow").style.display = "block";
    }
  } catch {
    document.getElementById("step1ConnRow").style.display = "block";
    setBadge("step1ConnBadge", "Backend not running. Start the server first.", "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
    </svg> Test Connection &amp; Continue`;
  }
});

/* ── STEP 2 · Model cards ───────────────────────────────────── */
document.querySelectorAll(".model-card").forEach((card) => {
  card.addEventListener("click", () => {
    document.querySelectorAll(".model-card").forEach((c) => c.classList.remove("selected"));
    card.classList.add("selected");
    card.querySelector("input[type='radio']").checked = true;
  });
});

document.getElementById("backStep2").addEventListener("click", () => goToStep(1));

document.getElementById("nextStep2").addEventListener("click", async () => {
  const selected = document.querySelector("input[name='llmModel']:checked");
  if (!selected) return;
  await store({ [SK.groqModel]: selected.value });
  goToStep(3);
});

/* ── STEP 3 · Ollama setup ──────────────────────────────────── */
document.getElementById("backStep3").addEventListener("click", () => goToStep(2));

// Copy command
document.getElementById("copyCmd").addEventListener("click", () => {
  const cmd = document.getElementById("ollamaCmd").textContent;
  navigator.clipboard.writeText(cmd).then(() => {
    const btn = document.getElementById("copyCmd");
    btn.classList.add("copied");
    setTimeout(() => btn.classList.remove("copied"), 2000);
  });
});

// Finish setup → main app
document.getElementById("finishSetup").addEventListener("click", async () => {
  await store({ [SK.onboarded]: true });
  launchMainApp();
});

/* ── Settings gear → re-enter wizard ───────────────────────── */
document.getElementById("openSettings").addEventListener("click", async () => {
  await store({ [SK.onboarded]: false });
  showWizard();
  currentStep = 1;
  updateDots(1);
  // Reset all steps
  document.querySelectorAll(".step").forEach((s) => {
    s.classList.remove("active", "exit-left");
    s.style.display = "none";
  });
  const s1 = document.getElementById("step1");
  s1.style.display = "flex";
  s1.classList.add("active");
});

/* ── UI state toggles ───────────────────────────────────────── */
function showWizard() {
  document.getElementById("wizard").style.display  = "block";
  document.getElementById("mainApp").style.display = "none";
  document.getElementById("stepDots").style.display = "flex";
}

function launchMainApp() {
  document.getElementById("wizard").style.display   = "none";
  document.getElementById("mainApp").style.display  = "flex";
  document.getElementById("stepDots").style.display = "none";
  populateSettingsBar();
}

async function populateSettingsBar() {
  const data = await load(SK.groqModel, SK.domain, SK.language);
  const model = data[SK.groqModel] || "llama-3.3-70b-versatile";
  // Pretty-print model name
  const labels = {
    "llama-3.3-70b-versatile": "Llama 3.3 · 70B",
    "llama-3.1-8b-instant":     "Llama 3.1 · 8B",
    "mixtral-8x7b-32768":       "Mixtral 8x7B",
    "gemma2-9b-it":              "Gemma 2 · 9B",
  };
  document.getElementById("activeModelLabel").textContent =
    labels[model] || model;

  // Restore selects
  if (data[SK.domain])   document.getElementById("domainSelect").value  = data[SK.domain];
  if (data[SK.language]) document.getElementById("languageSelect").value = data[SK.language];
}

/* ── Save config selects on change ─────────────────────────── */
document.getElementById("domainSelect").addEventListener("change", (e) =>
  store({ [SK.domain]: e.target.value })
);
document.getElementById("languageSelect").addEventListener("change", (e) =>
  store({ [SK.language]: e.target.value })
);

/* ── ANALYZE ────────────────────────────────────────────────── */
document.getElementById("analyzeBtn").addEventListener("click", async () => {
  const resultDiv  = document.getElementById("result");
  const statusDiv  = document.getElementById("status");
  const statusText = document.getElementById("statusText");
  const analyzeBtn = document.getElementById("analyzeBtn");

  resultDiv.style.display = "none";
  resultDiv.textContent   = "";
  resultDiv.className     = "";
  statusDiv.style.display = "flex";
  analyzeBtn.disabled     = true;

  try {
    statusText.textContent = "Scraping conversation…";
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) throw new Error("No active tab found.");

    const bad = ["chrome:", "edge:", "about:", "file:"];
    if (bad.some((s) => tab.url.startsWith(s)))
      throw new Error("Cannot analyze this page. Open an AI chat tab first.");

    const injectionResults = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files:  ["content_script.js"],
    });

    const scraped = injectionResults?.[0]?.result;
    if (!scraped)               throw new Error("Failed to scrape conversation.");
    if (scraped.error)          throw new Error(scraped.error);
    if (!scraped.conversation?.length)
      throw new Error("No conversation found on this page.");

    const data  = await load(SK.groqApiKey, SK.groqModel, SK.domain, SK.language);
    const apiKey = data[SK.groqApiKey];
    if (!apiKey) throw new Error("No Groq API key found. Re-open setup via the gear icon.");

    statusText.textContent = "Sending to analysis backend…";

    const payload = {
      conversation: scraped.conversation,
      domain:       data[SK.domain]    || "education",
      language:     data[SK.language]  || "auto",
      llm_type:     "groq",
      api_key:      apiKey,
      model:        data[SK.groqModel] || "llama-3.3-70b-versatile",
    };

    const res = await fetch("http://127.0.0.1:8000/analyze", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Backend error: ${res.status}`);

    const text  = await res.text();
    const lines = text.split("\n").filter(Boolean);
    let finalOutput = "";
    let backendError = "";

    for (const line of lines) {
      try {
        const chunk = JSON.parse(line);
        if (chunk.final_output) finalOutput  = chunk.final_output;
        if (chunk.error)        backendError  = chunk.error;
        if (chunk.status)       statusText.textContent = chunk.status;
      } catch (_) {}
    }

    if (backendError) throw new Error(backendError);
    if (!finalOutput) throw new Error("No output returned from backend.");

    resultDiv.textContent   = finalOutput;
    resultDiv.style.display = "block";
  } catch (err) {
    resultDiv.textContent   = `Error: ${err.message}`;
    resultDiv.className     = "error";
    resultDiv.style.display = "block";
  } finally {
    statusDiv.style.display = "none";
    analyzeBtn.disabled     = false;
  }
});

/* ── Init: check if already onboarded ─────────────────────── */
document.addEventListener("DOMContentLoaded", async () => {
  const data = await load(SK.onboarded);
  if (data[SK.onboarded]) {
    launchMainApp();
  } else {
    showWizard();
  }
});
