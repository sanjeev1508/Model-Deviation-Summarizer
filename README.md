<div align="center">
  <img src="https://raw.githubusercontent.com/sanjeev1508/Model-Deviation-Summarizer/main/logo.png" alt="icon" width="100">
  <h1>Model Deviation Summarizer</h1>
</div>

**Model Deviation Summarizer** is a browser extension that analyzes your AI conversations (ChatGPT, Gemini, Claude, Perplexity), detects where the model drifted from your original intent, and generates a professional-grade **Master Diagnostic Report** with a corrected Expert Prompt.

## Features

- **Master Diagnostic Report**: Structured, evidence-based analysis covering Deviation Summary, Root Cause Analysis, Drift Location, Evidence, What the Model Misunderstood, Fix Strategy, and a Reconstructed Expert Prompt.
- **Onboarding Wizard**: A streamlined 3-step UI to configure your API keys, select your preferred model, and setup local embeddings.
- **Bring Your Own Model (BYOM)**: Choose between state-of-the-art Groq models directly from the extension (Llama 3.3 70B, Llama 3.1 8B, Mixtral 8x7B, Gemma 2 9B).
- **Embedded Local Analysis**: Secure, private, and offline semantic similarity scoring via Ollama embedding models (`nomic-embed-text`) or fallback `sentence-transformers`.
- **Structured Payload Reasoning**: The LLM receives a deterministic JSON payload (metrics, drift_analysis, keyword_analysis, constraint_analysis, sentence_alignment) — drastically reducing hallucination.
- **Multilingual Support**: English, Tamil, and Hindi, with automatic language detection.
- **Multi-Platform**: Works transparently on ChatGPT, Google Gemini, Claude.ai, and Perplexity.ai.
- **Domain-Aware Analysis**: Adjusts context dynamically for Education, Healthcare, Banking, Legal, and Engineering prompts.

## How the Pipeline Works

```
Conversation (browser)
       │
       ▼
[1] Local Embeddings (Ollama / sentence-transformers)
    → semantic_similarity, keyword_overlap,
      sentence_alignment[], drift_point, severity
       │
       ▼
[2] Groq LLM — Structured Extraction
    → extracted context, intent alignment,
      constraint scores, keyword analysis
       │
       ▼
[3] Assemble Master Payload (pure Python)
    → JSON matching the MASTER_PROMPT schema
       │
       ▼
[4] Groq LLM — MASTER_PROMPT
    → Full Diagnostic Report + Reconstructed Expert Prompt
```

Only **2 LLM calls** total. All reasoning is grounded in deterministic, structued metrics calculated locally.

## Prerequisites

1. **Python 3.9+**
2. **Groq API Key** — free at [console.groq.com](https://console.groq.com)
3. **Ollama** (Optional but Recommended) — local embeddings via `nomic-embed-text`
4. **Google Chrome or Microsoft Edge**

## Quick Start

```bash
git clone https://github.com/sanjeev1508/Model-Deviation-Summarizer.git
cd Model-Deviation-Summarizer/app

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
uvicorn main:app --reload
```

Then load the `extension/` folder as an unpacked Chrome extension.

## Setup Wizard

When you open the extension for the first time, you'll be greeted by a 3-step setup Wizard:

1. **Connect to Groq**: Paste your Groq API key to authenticate the backend securely.
2. **Choose Your Model**: Select from recommended models like **Llama 3.3 70B** or **Mixtral 8x7B**.
3. **Local Embeddings**: Install Ollama and pull `nomic-embed-text` to run latency-free, offline semantic embeddings.

## Installation

### 1. Backend Setup

```bash
pip install -r requirements.txt
```

Optionally configure `.env` from `.env.example` if you prefer to define defaults server-side:

```env
GROQ_API_KEY=your_key_here          # optional if entered via extension UI
GROQ_MODEL=llama-3.3-70b-versatile  # default if not chosen in UI
```

> The UI-configured settings always take priority over the `.env` fallback.

### 2. Start the Backend

```bash
uvicorn main:app --reload
```

Backend runs at `http://127.0.0.1:8000`.

### 3. Load the Extension

1. Open Chrome/Edge → `chrome://extensions`
2. Enable **Developer Mode** (top right)
3. Click **Load unpacked** → select the `extension/` folder

## Usage

1. Start the backend (`uvicorn main:app --reload`)
2. Open any supported AI chat tab (ChatGPT, Gemini, etc.) and hold a conversation
3. Click the extension icon and run through the Onboarding Setup if you haven't.
4. Click **Analyze Active Tab**.
5. Wait for the extraction and streaming pipeline to generate your Master Diagnostic Report.

## Extension Settings

| Setting | Options | Default |
|---|---|---|
| Domain | Education · Healthcare · Banking · Legal · Engineering | Education |
| Response Language | Auto-detect · English · Tamil · Hindi | Auto-detect |

Both settings can be changed at any time using the Settings Bar at the top of the extension's Main App screen.

## Project Structure

```
app/
├── extension/
│   ├── manifest.json           # Extension manifest
│   ├── popup.html              # Extension Wizard & UI
│   ├── popup.js                # Extension logic, state management, UI transitions
│   ├── content_script.js       # Conversation scraper (ChatGPT, Gemini, etc.)
│   └── style.css               # Professional Design System & Transitions
├── main.py                     # FastAPI backend & pipeline orchestration
├── deviation_service.py        # Embeddings, per-turn metrics, drift detection
├── reconstruction_service.py   # MASTER_PROMPT + generate_master_report()
├── summary_service.py          # Language detection & LANGUAGE_NAMES
├── embedding_service.py        # Embedding handling
├── groq_client.py              # Groq client factory (UI key > .env fallback)
├── models.py                   # Pydantic request/response models
├── config.py                   # .env loader
└── requirements.txt
```

## Privacy

Conversation text is extracted by the content script in your browser and sent to your **local** backend (`localhost:8000`), which manages embedding analysis locally, and then calls the Groq API securely. Your Groq API key is saved only in your browser's local extension storage (`chrome.storage.local`). No telemetry is collected.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
