from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json
from models import (
    ChatRequest,
    IntegratedResponse
)
from deviation_service import analyze_conversation, evaluate_deviations
from summary_service import build_conversation_text, summarize_transcript
from reconstruction_service import generate_expert_prompt
from fastapi.middleware.cors import CORSMiddleware


import config

app = FastAPI(title="Conversation Alignment Engine")

# ==========================================
# Integrated Workflow API
# ==========================================

@app.get("/config")
def get_config():
    api_source = "Unknown"
    if config.NVIDIA_API_KEY:
        api_source = "NVIDIA API"
    elif config.BASE_URL and "openai" in config.BASE_URL:
        api_source = "OpenAI API"
    elif config.BASE_URL and "deepseek" in config.BASE_URL: # Example check
        api_source = "Deepseek API" # Example check
    elif config.BASE_URL:
         api_source = "Custom/Other API"

    return {
        "model_name": config.MODEL_NAME,
        "embed_model": config.EMBED_MODEL,
        "api_source": api_source,
        "ollama_url": config.OLLAMA_BASE_URL
    }


@app.post("/analyze")
async def analyze(chat: ChatRequest):
    return StreamingResponse(analyze_stream(chat), media_type="application/x-ndjson")

async def analyze_stream(chat: ChatRequest):
    # Extract config
    config = {
        "embedding_model": chat.embedding_model,
        "embedding_provider": chat.embedding_provider,
        "embedding_api_key": chat.embedding_api_key,
        "llm_type": chat.llm_type,
        "api_key": chat.api_key,
        "base_url": chat.base_url,
        "model_name": chat.model_name
    }

    # 1. Pre-Processing & Embedding Status
    yield json.dumps({"status": "Preprocessing & Embedding..."}) + "\n"
    
    # 2. Deviation Analysis
    try:
        features = analyze_conversation(chat.dict(), config=config)
        yield json.dumps({"status": "Analyzing Deviations..."}) + "\n"
    except Exception as e:
        yield json.dumps({"error": str(e)}) + "\n"
        return

    # 3. Transcript Summary
    conversation_text = build_conversation_text(chat.dict())
    yield json.dumps({"status": "Summarizing Conversation..."}) + "\n"
    summary_text = summarize_transcript(conversation_text, config=config)

    # 4. Insights Extraction
    yield json.dumps({"status": "Extracting User Expectations..."}) + "\n"
    try:
        deviation_insights_json = evaluate_deviations(conversation_text, config=config)
        deviation_insights = json.loads(deviation_insights_json)
    except Exception as e:
        print(f"Error evaluating deviations: {e}")
        deviation_insights = {}

    # 5. Expert Prompt Generation
    yield json.dumps({"status": "Generating Comprehensive Analysis..."}) + "\n"
    expert_prompt = generate_expert_prompt(
        summary_text, 
        features["conversation_metrics"],
        deviation_insights,
        config=config
    )

    # 6. Final Result
    yield json.dumps({"final_output": expert_prompt}) + "\n"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
