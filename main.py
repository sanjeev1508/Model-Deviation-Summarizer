from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import traceback
import asyncio
from pydantic import BaseModel as PydanticBase

from models import ChatRequest
from deviation_service import analyze_conversation, extract_keyword_constraint_analysis
from summary_service import build_conversation_text, detect_language, LANGUAGE_NAMES
from reconstruction_service import generate_master_report, DOMAIN_PERSONAS
from groq_client import get_groq_client, get_groq_model
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
    return {
        "groq_model":         app_config.GROQ_MODEL,
        "embed_model":        app_config.EMBED_MODEL,
        "domain":             app_config.DOMAIN,
        "supported_languages": app_config.SUPPORTED_LANGUAGES,
        "api_source":         "Groq API",
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
    runtime_config = chat.get_runtime_config()

    try:
        # ── Step 1: Embedding-based alignment metrics ──────────────────────
        yield json.dumps({"status": "Embedding & computing alignment metrics..."}) + "\n"

        features = await asyncio.to_thread(
            analyze_conversation,
            chat.model_dump(),
            runtime_config,
        )

        # ── Step 2: LLM → keyword / constraint / intent extraction ─────────
        yield json.dumps({"status": "Extracting keywords, constraints & intent..."}) + "\n"

        conversation_text = build_conversation_text(chat.model_dump())

        kc_data = await asyncio.to_thread(
            extract_keyword_constraint_analysis,
            conversation_text,
            runtime_config,
        )

        # ── Step 3: Build structured payload for the MASTER_PROMPT ─────────
        yield json.dumps({"status": "Building structured deviation payload..."}) + "\n"

        metrics = features.get("conversation_metrics", {})
        agg     = features.get("aggregate", {})

        master_payload = {
            "original_query":      kc_data.get("original_query", ""),
            "model_response":      kc_data.get("model_response", ""),
            "metrics": {
                "semantic_similarity": agg.get("semantic_similarity", 0.0),
                "intent_alignment":    kc_data.get("intent_alignment", 0.0),
                "keyword_overlap":     agg.get("keyword_overlap", 0.0),
                "constraint_score":    kc_data.get("constraint_score", 0.0),
            },
            "drift_analysis":      features.get("drift_analysis", {}),
            "keyword_analysis":    kc_data.get("keyword_analysis", {}),
            "constraint_analysis": kc_data.get("constraint_analysis", {}),
            "sentence_alignment":  features.get("sentence_alignment", []),
        }

        # ── Step 4: MASTER_PROMPT → final diagnostic report ────────────────
        yield json.dumps({"status": "Generating Master Diagnostic Report..."}) + "\n"

        final_output = await asyncio.to_thread(
            generate_master_report,
            master_payload,
            runtime_config,
        )

        yield json.dumps({"final_output": final_output}) + "\n"

    except Exception as e:
        traceback.print_exc()
        yield json.dumps({"error": str(e)}) + "\n"


# =====================================================
# Test Groq Connection
# =====================================================

class GroqTestRequest(PydanticBase):
    api_key: str | None = None


@app.post("/test-groq")
def test_groq(req: GroqTestRequest):
    try:
        runtime_config = {"api_key": req.api_key} if req.api_key else {}
        client = get_groq_client(runtime_config)
        model  = get_groq_model(runtime_config)
        resp   = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say: connection OK"}],
            max_tokens=10,
        )
        return {"ok": True, "model": model, "reply": resp.choices[0].message.content}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =====================================================
# Test Ollama Availability
# =====================================================

import httpx

@app.get("/test-ollama")
async def test_ollama():
    """Check if Ollama is running and nomic-embed-text is available."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://127.0.0.1:11434/api/tags")
        if resp.status_code != 200:
            return {"ok": False, "error": f"Ollama returned status {resp.status_code}"}
        data   = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        has_embed = any("nomic-embed-text" in m for m in models)
        return {"ok": True, "models": models, "has_embed": has_embed}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =====================================================
# Domain Chat (Live assistant)
# =====================================================

class DomainChatRequest(PydanticBase):
    message:  str
    domain:   str  = "education"
    language: str  = "auto"
    history:  list = []


@app.post("/chat")
def domain_chat(req: DomainChatRequest):
    runtime_config = {"domain": req.domain}
    client = get_groq_client(runtime_config)
    model  = get_groq_model(runtime_config)
    domain = req.domain

    lang      = req.language if req.language != "auto" else detect_language(req.message)
    lang_name = LANGUAGE_NAMES.get(lang, "English")

    persona = DOMAIN_PERSONAS.get(domain, DOMAIN_PERSONAS["education"])
    system = f"""{persona}

You are a multilingual assistant. The user is communicating in {lang_name}.
Always respond in {lang_name} unless they switch languages.
Be accurate, empathetic, and domain-focused.
"""

    messages = [{"role": "system", "content": system}]
    messages.extend(req.history)
    messages.append({"role": "user", "content": req.message})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.5,
            max_tokens=1024,
        )
        reply = response.choices[0].message.content.strip()
        return {
            "reply":    reply,
            "language": lang_name,
            "domain":   domain,
            "model":    model,
        }
    except Exception as e:
        return {"error": str(e)}