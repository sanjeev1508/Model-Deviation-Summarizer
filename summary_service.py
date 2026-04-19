"""
Text Summarization Service
- Abstractive summarization via Groq LLM
- Supports English, Tamil, Hindi (detected automatically)
"""
from groq_client import get_groq_client, get_groq_model
from langdetect import detect, LangDetectException
import config as app_config

LANGUAGE_NAMES = {
    "en": "English",
    "ta": "Tamil",
    "hi": "Hindi",
}

SUMMARY_PROMPTS = {
    "en": """You are a strict transcript summarizer.
Rules:
- Identify the User's core objective and any shifts in intent.
- Highlight where the Model's responses missed the mark.
- Concise: Maximum 300 words.
- Format: "User wanted X. Model provided Y. User corrected with Z..."
Respond in English.""",
    "ta": """நீங்கள் ஒரு உரையாடல் சுருக்கி.
விதிகள்:
- பயனர் என்ன விரும்பினார், மாதிரி எங்கு தவறானது என்று விளக்கவும்.
- அதிகபட்சம் 300 வார்த்தைகள்.
தமிழில் பதில் அளிக்கவும்.""",
    "hi": """आप एक वार्तालाप सारांशकर्ता हैं।
नियम:
- उपयोगकर्ता का मूल उद्देश्य और मॉडल की विफलताएं बताएं।
- अधिकतम 300 शब्द।
हिंदी में उत्तर दें।""",
}

def build_conversation_text(chat: dict) -> str:
    text = ""
    for msg in chat["conversation"]:
        text += f"{msg['role'].upper()}:\n{msg['content']}\n\n"
    return text.strip()


def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return lang if lang in app_config.SUPPORTED_LANGUAGES else "en"
    except LangDetectException:
        return "en"


def summarize_transcript(conversation_text: str, runtime_config: dict | None = None) -> str:
    lang = (runtime_config or {}).get("language")
    if not lang or lang == "auto":
        lang = detect_language(conversation_text)
    if lang not in app_config.SUPPORTED_LANGUAGES:
        lang = "en"

    system_prompt = SUMMARY_PROMPTS.get(lang, SUMMARY_PROMPTS["en"])
    client = get_groq_client(runtime_config)
    model = get_groq_model(runtime_config)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": conversation_text},
        ],
        temperature=0.1,
        max_tokens=512,
    )
    summary = response.choices[0].message.content.strip()
    lang_label = LANGUAGE_NAMES.get(lang, "English")
    return f"[Detected Language: {lang_label}]\n\n{summary}"

