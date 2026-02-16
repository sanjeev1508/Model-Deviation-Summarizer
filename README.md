# Model Deviation Summarizer

**Model Deviation Summarizer** is an Edge extension designed to analyze conversations with AI models (ChatGPT, Gemini, Claude, Perplexity) and detect deviations from your original intent. It uses local LLMs (via Ollama) to analyze the chat transcript, identify shifts in context or tone, and reconstruct a highly optimized "Expert Prompt" to help you get back on track.

![Extension UI](https://via.placeholder.com/600x400?text=Model+Deviation+Summarizer+UI)

## Features

-   **Local-First Privacy**: Runs entirely with local models (Ollama). No data leaves your machine unless you explicitly configure an API.
-   **Deviation Analysis**: Detects when and how an AI model drifted from your original request.
-   **Vector-Based Metrics**: Calculates Semantic Alignment and Expectation Alignment scores.
-   **Expert Prompt Reconstruction**: Automatically generates a refined, improved prompt based on the analysis to fix the deviation in a new session.
-   **Multi-Platform Support**: Works on:
    -   ChatGPT
    -   Google Gemini
    -   Claude.ai
    -   Perplexity.ai
-   **Professional UI**: Clean, dark-themed interface for distraction-free analysis.

## Prerequisites

1.  **Ollama**: You must have [Ollama](https://ollama.com/) installed and running.
    -   Pull the embedding model: `ollama pull nomic-embed-text`
    -   Pull the LLM: `ollama pull llama3` (or your preferred model)
2.  **Python 3.8+**: For the backend analysis engine.
3.  **Google Chrome or Microsoft Edge**: To install the extension.

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/sanjeev1508/Model-Deviation-Summarizer.git
cd Model-Deviation-Summarizer/app
```

### 2. Setup Backend
Create a virtual environment and install dependencies:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```
*Note: Ensure `requirements.txt` includes `fastapi`, `uvicorn`, `requests`, `numpy`, `scikit-learn`, `nltk`, `openai`.*

### 3. Load Extension
1.  Open Chrome/Edge and navigate to `chrome://extensions`.
2.  Enable **Developer Mode** (top right).
3.  Click **Load unpacked**.
4.  Select the `extension` folder inside the `app` directory.

## Usage

1.  **Start the Backend**:
    ```bash
    uvicorn main:app --reload
    ```
    The backend will run at `http://127.0.0.1:8000`.

2.  **Open a Chat**:
    Go to ChatGPT, Gemini, or Perplexity and have a conversation.

3.  **Analyze**:
    -   Click the extension icon.
    -   Configure your Local Ollama models (defaults are usually fine).
    -   Click **Analyze Active Tab**.
    -   Wait for the "Comprehensive Deviation Report".

## Project Structure

```
app/
├── extension/          # Browser extension source (manifest, popup, content script)
├── main.py             # FastAPI backend entry point
├── deviation_service.py # Core logic for embeddings & vector analysis
├── summary_service.py   # Transcript summarization logic
├── reconstruction_service.py # Prompt optimization logic
├── models.py           # Pydantic data models
└── requirements.txt    # Python dependencies
```

## Privacy

This tool allows you to use **100% Local Models**. Your chat data is extracted by the extension and sent ONLY to your local Python backend (`localhost:8000`). It is not stored or sent to any third-party cloud unless you modify the code to do so.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
