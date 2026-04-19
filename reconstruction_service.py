"""
Master Prompt Reconstruction Service.
Sends a fully structured payload to the MASTER_PROMPT for deterministic,
evidence-based deviation reports + expert prompt reconstruction.
"""
import json
from groq_client import get_groq_client, get_groq_model, get_domain


# ── Domain personas (used as preamble before the master prompt) ────────────

DOMAIN_PERSONAS = {
    "education": "You are an expert educational consultant and curriculum designer with deep pedagogical knowledge.",
    "healthcare": "You are a senior medical advisor with expertise in clinical decision support and patient communication.",
    "banking":    "You are a seasoned banking and financial advisor with expertise in personal finance and regulatory compliance.",
}

# ── Master Prompt ──────────────────────────────────────────────────────────

MASTER_PROMPT = """You are an advanced AI Conversation Debugger and Deviation Analysis Engine.

Your task is to analyze a conversation between a USER and an AI MODEL, detect deviations from the user's original intent, and produce a structured, evidence-based diagnostic report along with an improved expert-level prompt.

You MUST NOT rely on vague explanations. You MUST reason strictly based on the provided structured metrics and text.

---

### INPUT SCHEMA

You will receive a JSON payload with:
- original_query       : The user's initial request
- model_response       : The AI's first response
- metrics              : semantic_similarity, intent_alignment, keyword_overlap, constraint_score (all 0–1)
- drift_analysis       : drift_point (sentence index or "none"), severity ("low" | "moderate" | "high")
- keyword_analysis     : expected_keywords, actual_keywords
- constraint_analysis  : missing_constraints (list)
- sentence_alignment   : per-turn cosine similarity scores (list of floats)

---

### TASK

Perform a deep diagnostic analysis and generate a structured report.

---

### OUTPUT FORMAT (STRICT)

## Deviation Summary
Clearly state whether the model deviated from the user's intent.
Classify severity: Aligned / Minor / Moderate / Severe.

## Root Cause Analysis
Explain WHY the deviation happened using:
- intent mismatch
- topic drift
- missing constraints
- ambiguity

## Drift Location
Identify EXACTLY where the deviation starts (sentence number or reasoning shift).

## Evidence
Use:
- keyword mismatch
- sentence alignment drops
- metric values

## What the Model Misunderstood
Be precise. Do not generalize.

## Fix Strategy
Explain how the user should modify their prompt to avoid this issue.

## Reconstructed Expert Prompt
Generate a highly optimized prompt that:
- preserves original intent
- adds missing constraints
- removes ambiguity
- prevents the observed deviation

The prompt MUST be:
- clear
- structured
- unambiguous
- domain-correct

---

### RULES
- Do NOT hallucinate information not present in the input JSON
- Do NOT repeat the input verbatim
- Do NOT give generic advice
- Always ground your reasoning in the provided metrics
- Be concise but highly informative
- Prioritize clarity and actionability

---

### GOAL
Transform raw deviation signals into a professional-grade AI debugging report and a corrected, expert-level prompt.
"""

MULTILANG_INSTRUCTION = """
IMPORTANT: Detect the primary language of the conversation (English / Tamil / Hindi).
Generate the expert prompt AND the analysis in THAT SAME LANGUAGE.
If the conversation mixes languages, use English.
"""


# ── Main entry point ───────────────────────────────────────────────────────

def generate_master_report(
    payload: dict,
    runtime_config: dict | None = None,
) -> str:
    """
    Sends the structured payload to llama-3.3-70b-versatile using the MASTER_PROMPT.
    payload must contain all keys defined in the MASTER_PROMPT INPUT SCHEMA.
    """
    domain  = get_domain(runtime_config)
    persona = DOMAIN_PERSONAS.get(domain, DOMAIN_PERSONAS["education"])

    client = get_groq_client(runtime_config)
    model  = get_groq_model(runtime_config)

    system_prompt = f"{persona}\n\n{MASTER_PROMPT}\n\n{MULTILANG_INSTRUCTION}"

    user_content = f"""INPUT:
{json.dumps(payload, indent=2, ensure_ascii=False)}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ],
        temperature=0.3,
        max_tokens=2000,
    )
    return response.choices[0].message.content.strip()
