import json
from deviation_service import analyze_conversation, evaluate_deviations
from summary_service import build_conversation_text, summarize_transcript
from reconstruction_service import generate_expert_prompt


def main(context):
    """
    Appwrite Function entrypoint.
    Deploy this file as the function entrypoint in appwrite.json.
    Trigger via async execution (async=true) from the extension to bypass
    the 30-second synchronous timeout.
    """
    try:
        # ── Parse request body ──────────────────────────────────────────
        try:
            body = json.loads(context.req.body or "{}")
        except json.JSONDecodeError:
            return context.res.json({"error": "Invalid JSON body"}, status_code=400)

        if not body.get("conversation"):
            return context.res.json({"error": "Missing 'conversation' in request body"}, status_code=400)

        # ── Extract runtime config ──────────────────────────────────────
        runtime_config = {
            "embedding_model":    body.get("embedding_model"),
            "embedding_provider": body.get("embedding_provider"),
            "embedding_api_key":  body.get("embedding_api_key"),
            "llm_type":           body.get("llm_type"),
            "api_key":            body.get("api_key"),
            "base_url":           body.get("base_url"),
            "model_name":         body.get("model_name"),
            "ollama_url":         body.get("ollama_url"),
        }

        context.log("Step 1/4: Preprocessing & Embedding...")
        features = analyze_conversation(body, config=runtime_config)

        context.log("Step 2/4: Summarizing Conversation...")
        conversation_text = build_conversation_text(body)
        summary_text = summarize_transcript(conversation_text, config=runtime_config)

        context.log("Step 3/4: Extracting User Expectations...")
        try:
            deviation_raw = evaluate_deviations(conversation_text, config=runtime_config)
            deviation_insights = json.loads(deviation_raw)
        except Exception as e:
            context.error(f"Deviation extraction failed (non-fatal): {e}")
            deviation_insights = {}

        context.log("Step 4/4: Generating Comprehensive Analysis...")
        expert_prompt = generate_expert_prompt(
            summary_text,
            features.get("conversation_metrics", {}),
            deviation_insights,
            config=runtime_config
        )

        context.log("Analysis complete.")
        return context.res.json({"final_output": expert_prompt})

    except Exception as e:
        context.error(f"Fatal error: {e}")
        return context.res.json({"error": str(e)}, status_code=500)
