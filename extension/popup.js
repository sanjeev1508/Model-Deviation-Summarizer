// ─────────────────────────────────────────────────────────────────────────────
// Appwrite Configuration
// ⚠️ Only APPWRITE_PROJECT_ID needs to be set — everything else is filled in.
// Find it: Appwrite Console → Your Project → Settings → Project ID
// ─────────────────────────────────────────────────────────────────────────────
const APPWRITE_ENDPOINT = "https://fra.cloud.appwrite.io/v1";
const APPWRITE_PROJECT_ID = "69a079db0038bb4144b3";
const APPWRITE_FUNCTION_ID = "69a07b06000beb07e7c2";

// ─────────────────────────────────────────────────────────────────────────────
// Appwrite SDK setup (uses bundled appwrite.js loaded before this script)
// ─────────────────────────────────────────────────────────────────────────────
const appwriteClient = new Appwrite.Client()
    .setEndpoint(APPWRITE_ENDPOINT)
    .setProject(APPWRITE_PROJECT_ID);

const appwriteFunctions = new Appwrite.Functions(appwriteClient);

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

    let msgCycler = null;

    try {
        // ── 1. Get active tab ────────────────────────────────────────────────
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab) throw new Error("No active tab found.");

        const invalidSchemes = ['chrome:', 'edge:', 'about:', 'file:'];
        if (invalidSchemes.some(s => tab.url.startsWith(s)))
            throw new Error("Cannot analyze this page type.");

        // ── 2. Scrape conversation ───────────────────────────────────────────
        const injectionResults = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content_script.js']
        });

        if (!injectionResults?.[0]?.result)
            throw new Error("Failed to scrape conversation. Ensure you are on a supported chatbot page.");

        const scrapedData = injectionResults[0].result;
        if (scrapedData.error) throw new Error(scrapedData.error);
        if (!scrapedData.conversation || scrapedData.conversation.length === 0)
            throw new Error("No conversation found. Please ensure the chat is loaded.");

        // ── 3. Build payload ─────────────────────────────────────────────────
        const config = getConfigPayload();
        saveConfigToStorage();
        const payload = { ...scrapedData, ...config };

        // ── 4. Trigger Appwrite async execution (SDK handles CORS) ───────────
        statusText.textContent = "Sending to Analysis Engine...";

        const execution = await appwriteFunctions.createExecution(
            APPWRITE_FUNCTION_ID,
            JSON.stringify(payload),  // body
            true                      // async = true → bypasses 30s timeout
        );

        const executionId = execution.$id;
        if (!executionId) throw new Error("No executionId returned from Appwrite.");

        // ── 5. Poll for result ───────────────────────────────────────────────
        const statusMessages = [
            "Preprocessing & Embedding...",
            "Analyzing Deviations...",
            "Summarizing Conversation...",
            "Extracting User Expectations...",
            "Generating Comprehensive Analysis...",
        ];
        let msgIdx = 0;
        statusText.textContent = statusMessages[0];
        msgCycler = setInterval(() => {
            msgIdx = (msgIdx + 1) % statusMessages.length;
            statusText.textContent = statusMessages[msgIdx];
        }, 5000);

        let finalOutput = null;
        const MAX_POLLS = 60;   // 60 × 5s = 5 minutes max
        const POLL_INTERVAL_MS = 5000;

        for (let i = 0; i < MAX_POLLS; i++) {
            await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));

            let poll;
            try {
                poll = await appwriteFunctions.getExecution(APPWRITE_FUNCTION_ID, executionId);
            } catch (_) {
                continue; // transient error — keep polling
            }

            const status = poll.status; // "waiting" | "processing" | "completed" | "failed"

            if (status === "completed") {
                clearInterval(msgCycler);
                const body = JSON.parse(poll.responseBody || "{}");
                if (body.error) throw new Error(body.error);
                finalOutput = body.final_output;
                break;
            }

            if (status === "failed") {
                clearInterval(msgCycler);
                const body = JSON.parse(poll.responseBody || "{}");
                throw new Error(`Analysis failed: ${body.error || poll.errors || "Unknown error"}`);
            }
            // "waiting" | "processing" → keep polling
        }

        if (msgCycler) clearInterval(msgCycler);
        if (!finalOutput) throw new Error("Analysis timed out. Try a shorter conversation.");

        // ── 6. Display result ────────────────────────────────────────────────
        resultDiv.textContent = finalOutput;
        resultDiv.style.display = 'block';

    } catch (error) {
        if (msgCycler) clearInterval(msgCycler);
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
