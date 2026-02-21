from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import traceback

from models import ChatRequest
from deviation_service import analyze_conversation, evaluate_deviations
from summary_service import build_conversation_text, summarize_transcript
from reconstruction_service import generate_expert_prompt
import config as app_config


app = FastAPI(title="Conversation Alignment Engine")

# =====================================================
# CORS (Required for Browser Extension)
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Safe for extension usage
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# Health Check Route (Prevents 404 on root)
# =====================================================

@app.get("/")
def health_check():
    return {"status": "Backend is running"}

# =====================================================
# Config Inspection Route
# =====================================================

@app.get("/config")
def get_config():
    api_source = "Unknown"

    if app_config.NVIDIA_API_KEY:
        api_source = "NVIDIA API"
    elif app_config.BASE_URL and "openai" in app_config.BASE_URL:
        api_source = "OpenAI API"
    elif app_config.BASE_URL and "deepseek" in app_config.BASE_URL:
        api_source = "Deepseek API"
    elif app_config.BASE_URL:
        api_source = "Custom/Other API"

    return {
        "model_name": app_config.MODEL_NAME,
        "embed_model": app_config.EMBED_MODEL,
        "api_source": api_source,
        "ollama_url": app_config.OLLAMA_BASE_URL
    }

# =====================================================
# Streaming Analyze Endpoint
# =====================================================

@app.post("/analyze")
async def analyze(chat: ChatRequest):
    return StreamingResponse(
        analyze_stream(chat),
        media_type="application/x-ndjson"
    )


async def analyze_stream(chat: ChatRequest):

    # Extract runtime config safely
    runtime_config = {
        "embedding_model": chat.embedding_model,
        "embedding_provider": chat.embedding_provider,
        "embedding_api_key": chat.embedding_api_key,
        "llm_type": chat.llm_type,
        "api_key": chat.api_key,
        "base_url": chat.base_url,
        "model_name": chat.model_name
    }

    try:
        # 1️⃣ Preprocessing
        yield json.dumps({"status": "Preprocessing & Embedding..."}) + "\n"

        features = analyze_conversation(
            chat.model_dump(),
            config=runtime_config
        )

        yield json.dumps({"status": "Analyzing Deviations..."}) + "\n"

        # 2️⃣ Build conversation text
        conversation_text = build_conversation_text(chat.model_dump())

        # 3️⃣ Summary
        yield json.dumps({"status": "Summarizing Conversation..."}) + "\n"
        summary_text = summarize_transcript(
            conversation_text,
            config=runtime_config
        )

        # 4️⃣ Extract deviation insights
        yield json.dumps({"status": "Extracting User Expectations..."}) + "\n"

        try:
            deviation_insights_json = evaluate_deviations(
                conversation_text,
                config=runtime_config
            )
            deviation_insights = json.loads(deviation_insights_json)
        except Exception:
            deviation_insights = {}

        # 5️⃣ Generate final expert output
        yield json.dumps({"status": "Generating Comprehensive Analysis..."}) + "\n"

        expert_prompt = generate_expert_prompt(
            summary_text,
            features.get("conversation_metrics", {}),
            deviation_insights,
            config=runtime_config
        )

        # 6️⃣ Final output
        yield json.dumps({"final_output": expert_prompt}) + "\n"

    except Exception as e:
        traceback.print_exc()
        yield json.dumps({"error": str(e)}) + "\n"