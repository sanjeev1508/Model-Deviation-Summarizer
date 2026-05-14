"""
Appwrite Function entrypoint.

Mirrors the FastAPI /analyze pipeline (embedding metrics → keyword/constraint
extraction → master report) without streaming. Request body matches ChatRequest
fields used by the extension: conversation, domain, language, api_key, model,
embedding_model.

Deploy as the Appwrite function entrypoint. Use async execution (async=true)
from the client if you need to exceed synchronous timeouts.
"""
import json
import traceback

from deviation_service import analyze_conversation, extract_keyword_constraint_analysis
from summary_service import build_conversation_text
from reconstruction_service import generate_master_report
from pipeline_core import build_master_payload


def _runtime_config(body: dict) -> dict:
    return {
        "embedding_model":   body.get("embedding_model"),
        "embedding_provider": body.get("embedding_provider"),
        "domain":          body.get("domain"),
        "language":        body.get("language"),
        "api_key":         body.get("api_key"),
        "model":           body.get("model"),
    }


def main(context):
    try:
        try:
            body = json.loads(context.req.body or "{}")
        except json.JSONDecodeError:
            return context.res.json({"error": "Invalid JSON body"}, status_code=400)

        if not body.get("conversation"):
            return context.res.json({"error": "Missing 'conversation' in request body"}, status_code=400)

        rc = _runtime_config(body)

        context.log("Step 1/3: Embedding & alignment metrics...")
        features = analyze_conversation(body, runtime_config=rc)

        context.log("Step 2/3: Keyword / constraint / intent extraction (Groq)...")
        conversation_text = build_conversation_text(body)
        kc_data = extract_keyword_constraint_analysis(conversation_text, runtime_config=rc)

        context.log("Step 3/3: Master diagnostic report (Groq)...")
        master_payload = build_master_payload(features, kc_data)
        final_output = generate_master_report(master_payload, runtime_config=rc)

        context.log("Analysis complete.")
        return context.res.json({"final_output": final_output})

    except Exception as e:
        traceback.print_exc()
        context.error(f"Fatal error: {e}")
        return context.res.json({"error": str(e)}, status_code=500)
