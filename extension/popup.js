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

    // Status message cycler
    const messages = [
        "Analyzing Deviation...",
        "Inferring Expectations...",
        "Summarizing Transcript...",
        "Reconstructing Prompt..."
    ];
    let msgIndex = 0;
    statusText.textContent = "Scraping Conversation...";

    let intervalId = null;

    try {
        // 1. Get the active tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab) {
            throw new Error("No active tab found.");
        }

        // 2. Execute the content script to scrape data
        const invalidSchemes = ['chrome:', 'edge:', 'about:', 'file:'];
        if (invalidSchemes.some(scheme => tab.url.startsWith(scheme))) {
            throw new Error("Cannot analyze this page type.");
        }

        const injectionResults = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content_script.js']
        });

        if (!injectionResults || !injectionResults[0] || !injectionResults[0].result) {
            throw new Error("Failed to scrape conversation. Ensure you are on a supported chatbot page.");
        }

        const scrapedData = injectionResults[0].result;

        if (scrapedData.error) {
            throw new Error(scrapedData.error);
        }

        if (!scrapedData.conversation || scrapedData.conversation.length === 0) {
            throw new Error("No conversation found. Please ensure the chat is loaded.");
        }

        // 3. Send to API with Streaming
        statusText.textContent = "Connecting to Analysis Engine...";

        // Collect config
        const config = getConfigPayload();

        // Save to usage for next time
        saveConfigToStorage();

        // Merge config into scraped data
        const payload = {
            ...scrapedData,
            ...config
        };

        const response = await fetch('https://model-deviation-summarizer-3.onrender.com/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        // Process the stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let finalResult = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const data = JSON.parse(line);
                    if (data.status) {
                        statusText.textContent = data.status;
                    } else if (data.final_output) {
                        finalResult = data.final_output;
                    } else if (data.error) {
                        throw new Error(data.error);
                    }
                } catch (e) {
                    console.error("Error parsing JSON chunk", e);
                }
            }
        }


        if (finalResult) {
            resultDiv.textContent = finalResult;
            resultDiv.style.display = 'block';
        } else {
            throw new Error("Analysis failed to produce output.");
        }

    } catch (error) {
        resultDiv.textContent = `Error: ${error.message}`;
        resultDiv.className = 'error';
        resultDiv.style.display = 'block';
    } finally {
        if (intervalId) clearInterval(intervalId);
        statusDiv.style.display = 'none';
        analyzeBtn.disabled = false;
    }
});

function getConfigPayload() {
    // Explicitly Local Only
    let config = {
        embedding_model: document.getElementById('embedModelLocal').value || "nomic-embed-text:latest",
        embedding_provider: "local",
        embedding_api_key: null,
        llm_type: "ollama",
        api_key: null,
        base_url: "http://localhost:11434/v1",
        model_name: document.getElementById('llmModelLocal').value || "llama3",
        ollama_url: "http://localhost:11434"
    };
    return config;
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
        btn.style.color = "#3b82f6"; // match accent
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.color = "";
        }, 1500);
    });
}

function loadConfigFromStorage() {
    chrome.storage.local.get(['uiConfig'], (result) => {
        if (result.uiConfig) {
            const data = result.uiConfig;
            if (data.embedModelLocal) document.getElementById('embedModelLocal').value = data.embedModelLocal;
            if (data.llmModelLocal) document.getElementById('llmModelLocal').value = data.llmModelLocal;
        }
    });
}

const saveBtn = document.getElementById('saveConfigBtn');
if (saveBtn) saveBtn.addEventListener('click', saveConfigToStorage);

document.addEventListener('DOMContentLoaded', loadConfigFromStorage);
