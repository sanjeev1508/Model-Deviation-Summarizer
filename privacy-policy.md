# Privacy Policy for Model Deviation Summarizer

**Effective Date:** April 29, 2026

## Overview
Model Deviation Summarizer ("the Extension") is designed to analyze AI chatbot conversations to detect model deviation and refine prompts. We take your privacy seriously. This policy explains what data is accessed, how it is used, and how it is protected.

## Data Collection and Usage
The Extension operates primarily on your local machine and interacts directly with third-party LLM providers (e.g., Groq) via an API key that you provide. 

**1. Conversation Data:**
* The Extension **only** reads the conversation text from supported AI chatbots (such as ChatGPT, Gemini, Claude, or Perplexity) when you actively click the "Analyze Active Tab" button.
* This conversation data is sent securely to the configured backend server (either your local `localhost` server or the provided Render backend) to be embedded and analyzed.
* The backend then forwards the necessary text to the Groq API (or your chosen LLM provider) to generate the diagnostic report.
* **We do not store, log, monitor, or sell any of your conversation data.** Once the analysis is returned to your browser, the data is discarded by our systems.

**2. API Keys and Settings:**
* Your Groq API key, selected model preferences, and domain settings are stored **locally** on your device using your browser's local extension storage (`chrome.storage.local`).
* These credentials are never sent to our servers for storage or tracking; they are only used to authenticate your direct requests to the AI provider.

## Third-Party Services
Because the Extension relies on external AI providers to function, your conversation data and prompts will be transmitted to them (e.g., Groq) during the analysis process. We encourage you to review the privacy policies of any third-party AI provider you choose to connect.

## Telemetry and Analytics
The Extension **does not** include any tracking scripts, analytics tools, or telemetry mechanisms. We do not track how you use the Extension, what you click, or how often you use it.

## Changes to This Policy
We may update this Privacy Policy from time to time. Any changes will be reflected in this document and updated in the project repository.

## Contact
If you have any questions or concerns about this Privacy Policy, please open an issue in the project repository on GitHub.
