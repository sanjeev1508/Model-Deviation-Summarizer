// ─────────────────────────────────────────────────────────────────────────────
// Appwrite Configuration
// ⚠️ Only replace YOUR_PROJECT_ID below — everything else is filled in.
// Find your Project ID: Appwrite Console → Your Project → Settings → Project ID
// ─────────────────────────────────────────────────────────────────────────────
const APPWRITE_ENDPOINT = "https://fra.cloud.appwrite.io/v1"; // Frankfurt region
const APPWRITE_PROJECT_ID = "YOUR_PROJECT_ID";                  // ← replace this
const APPWRITE_FUNCTION_ID = "69a07b06000beb07e7c2";             // from your domain

// ─────────────────────────────────────────────────────────────────────────────
// Analyze Button Handler
// ─────────────────────────────────────────────────────────────────────────────
document.getElementById('analyzeBtn').addEventListener('click', async () => {
    const resultDiv = document.getElementById('result');
    const statusDiv = document.getElementById('status');
    const statusText = document.getElementById('statusText');
    const analyzeBtn = document.getElementById('analyzeBtn');

    resultDiv.style.display = 'none';
    resultDiv.textContent = '';
    resultDiv.className = '';
    statusDiv.style.display = 'block';
    analyzeBtn.disabled = true;

    statusText.textContent = "Scraping Conversation...";

    try {
        // ── 1. Get active tab ────────────────────────────────────────────────
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab) throw new Error("No active tab found.");

        const invalidSchemes = ['chrome:', 'edge:', 'about:', 'file:'];
        if (invalidSchemes.some(s => tab.url.startsWith(s))) {
            throw new Error("Cannot analyze this page type.");
        }

        // ── 2. Scrape conversation ───────────────────────────────────────────
        const injectionResults = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content_script.js']
        });

        if (!injectionResults?.[0]?.result) {
            throw new Error("Failed to scrape conversation. Ensure you are on a supported chatbot page.");
        }

        const scrapedData = injectionResults[0].result;
        if (scrapedData.error) throw new Error(scrapedData.error);
        if (!scrapedData.conversation || scrapedData.conversation.length === 0) {
            throw new Error("No conversation found. Please ensure the chat is loaded.");
        }

        // ── 3. Build payload ─────────────────────────────────────────────────
        const config = getConfigPayload();
        saveConfigToStorage();
        const payload = { ...scrapedData, ...config };

        // ── 4. Trigger Appwrite async execution ──────────────────────────────
        statusText.textContent = "Sending to Analysis Engine...";

        const triggerRes = await fetch(
            `${APPWRITE_ENDPOINT}/functions/${APPWRITE_FUNCTION_ID}/executions`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Appwrite-Project": APPWRITE_PROJECT_ID,
                },
                body: JSON.stringify({
                    body: JSON.stringify(payload),
                    async: true       // ← key: returns immediately, bypasses 30s timeout
                })
            }
        );

        if (!triggerRes.ok) {
            const err = await triggerRes.json().catch(() => ({}));
            throw new Error(`Appwrite trigger error: ${err.message || triggerRes.statusText}`);
        }

        const { $id: executionId } = await triggerRes.json();
        if (!executionId) throw new Error("No executionId returned from Appwrite.");

        // ── 5. Poll for result ───────────────────────────────────────────────
        statusText.textContent = "Analyzing Deviations...";

        const statusMessages = [
            "Preprocessing & Embedding...",
            "Analyzing Deviations...",
            "Summarizing Conversation...",
            "Extracting User Expectations...",
            "Generating Comprehensive Analysis...",
        ];
        let msgIdx = 0;
        const msgCycler = setInterval(() => {
            msgIdx = (msgIdx + 1) % statusMessages.length;
            statusText.textContent = statusMessages[msgIdx];
        }, 5000);

        let finalOutput = null;
        const MAX_POLLS = 60;   // 60 × 5s = 5 minutes max
        const POLL_INTERVAL_MS = 5000;

        for (let i = 0; i < MAX_POLLS; i++) {
            await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));

            const pollRes = await fetch(
                `${APPWRITE_ENDPOINT}/functions/${APPWRITE_FUNCTION_ID}/executions/${executionId}`,
                {
                    headers: {
                        "X-Appwrite-Project": APPWRITE_PROJECT_ID,
                    }
                }
            );

            if (!pollRes.ok) continue;   // transient error — keep polling

            const execution = await pollRes.json();
            const status = execution.status;  // "waiting" | "processing" | "completed" | "failed"

            if (status === "completed") {
                clearInterval(msgCycler);
                try {
                    const responseBody = JSON.parse(execution.responseBody || "{}");
                    if (responseBody.error) throw new Error(responseBody.error);
                    finalOutput = responseBody.final_output;
                } catch (parseErr) {
                    throw new Error(`Failed to parse result: ${parseErr.message}`);
                }
                break;
            }

            if (status === "failed") {
                clearInterval(msgCycler);
                const errBody = JSON.parse(execution.responseBody || "{}");
                throw new Error(`Analysis failed: ${errBody.error || execution.errors || "Unknown error"}`);
            }
            // else "waiting" / "processing" → keep polling
        }

        clearInterval(msgCycler);

        if (!finalOutput) throw new Error("Analysis timed out. Try a shorter conversation.");

        // ── 6. Display result ────────────────────────────────────────────────
        resultDiv.textContent = finalOutput;
        resultDiv.style.display = 'block';

    } catch (error) {
        resultDiv.textContent = `Error: ${error.message}`;
        resultDiv.className = 'error';
        resultDiv.style.display = 'block';
    } finally {
        statusDiv.style.display = 'none';
        analyzeBtn.disabled = false;
    }
});

// ─────────────────────────────────────────────────────────────────────────────
// Config Helpers
// ─────────────────────────────────────────────────────────────────────────────
function getConfigPayload() {
    return {
        embedding_model: document.getElementById('embedModelLocal').value || "nomic-embed-text:latest",
        embedding_provider: "local",
        embedding_api_key: null,
        llm_type: "ollama",
        api_key: null,
        base_url: "http://127.0.0.1:11434/v1",
        model_name: document.getElementById('llmModelLocal').value || "llama3",
        ollama_url: "http://127.0.0.1:11434"
    };
}

function saveConfigToStorage() {
    const data = {
        embedModelLocal: document.getElementById('embedModelLocal').value,
        llmModelLocal: document.getElementById('llmModelLocal').value,
    };
    chrome.storage.local.set({ uiConfig: data }, () => {
        const btn = document.getElementById('saveConfigBtn');
        const originalText = btn.textContent;
        btn.textContent = "Saved!";
        btn.style.color = "#3b82f6";
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.color = "";
        }, 1500);
    });
}

function loadConfigFromStorage() {
    chrome.storage.local.get(['uiConfig'], (result) => {
        if (result.uiConfig) {
            const d = result.uiConfig;
            if (d.embedModelLocal) document.getElementById('embedModelLocal').value = d.embedModelLocal;
            if (d.llmModelLocal) document.getElementById('llmModelLocal').value = d.llmModelLocal;
        }
    });
}

const saveBtn = document.getElementById('saveConfigBtn');
if (saveBtn) saveBtn.addEventListener('click', saveConfigToStorage);

document.addEventListener('DOMContentLoaded', loadConfigFromStorage);
