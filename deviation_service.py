"""
Deviation analysis: embedding-based alignment (Groq API or optional local ST).
Produces a rich structured payload consumed by the Master Prompt.
"""
from groq_client import get_groq_client, get_groq_model
from embedding_service import embed_texts, cosine_similarity
import re


# ── Keyword helpers ────────────────────────────────────────────────────────

def _tokenize(text: str) -> set[str]:
    """Lower-cased alphabetic tokens, length > 2."""
    return {w for w in re.findall(r"[a-zA-Z\u0980-\u0fff\u0900-\u097f]+", text.lower()) if len(w) > 2}


def _keyword_overlap(a: str, b: str) -> float:
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta:
        return 0.0
    return round(len(ta & tb) / len(ta), 4)


# ── Per-turn embedding analysis ────────────────────────────────────────────

def analyze_conversation(chat: dict, runtime_config: dict | None = None) -> dict:
    """
    Returns conversation_metrics + per-sentence alignment data needed
    by the master prompt payload.
    """
    messages = chat.get("conversation", [])
    pairs: list[tuple[str, str]] = []

    i = 0
    while i < len(messages) - 1:
        if messages[i]["role"] == "user" and messages[i + 1]["role"] in {"assistant", "model"}:
            u = messages[i]["content"] or " "
            a = messages[i + 1]["content"] or " "
            pairs.append((u, a))
        i += 1

    turns: list[dict] = []
    sentence_alignment: list[float] = []

    if pairs:
        flat: list[str] = []
        for u, a in pairs:
            flat.extend([u, a])
        all_vecs = embed_texts(flat, runtime_config)
        for k, (user_text, asst_text) in enumerate(pairs):
            vu, va = all_vecs[2 * k], all_vecs[2 * k + 1]
            score = cosine_similarity(vu, va)
            kw = _keyword_overlap(user_text, asst_text)
            turns.append({
                "turn":               k + 1,
                "semantic_alignment": round(score, 4),
                "keyword_overlap":    kw,
                "deviation":          round(1.0 - score, 4),
            })
            sentence_alignment.append(round(score, 4))

    avg_alignment = sum(t["semantic_alignment"] for t in turns) / len(turns) if turns else 0.0
    avg_kw = sum(t["keyword_overlap"] for t in turns) / len(turns) if turns else 0.0

    # Drift: first sentence where alignment drops > 0.15 below average
    drift_point: str | int = "none"
    for idx, score in enumerate(sentence_alignment):
        if avg_alignment - score > 0.15:
            drift_point = idx
            break

    severity = "low"
    if avg_alignment < 0.5:
        severity = "high"
    elif avg_alignment < 0.75:
        severity = "moderate"

    return {
        "conversation_metrics": {
            "turns":             turns,
            "average_alignment": round(avg_alignment, 4),
            "total_turns":       len(turns),
        },
        "sentence_alignment": sentence_alignment,
        "drift_analysis": {
            "drift_point": drift_point,
            "severity":    severity,
        },
        "aggregate": {
            "semantic_similarity": round(avg_alignment, 4),
            "keyword_overlap":     round(avg_kw, 4),
        },
    }


# ── Structured keyword + constraint extraction via LLM ─────────────────────

def extract_keyword_constraint_analysis(
    conversation_text: str,
    runtime_config: dict | None = None,
) -> dict:
    """
    One lightweight LLM call to extract:
    - expected_keywords, actual_keywords
    - missing_constraints
    - intent_alignment score (0-1)
    - constraint_score (0-1)
    - original_query, model_response (first turn)
    """
    client = get_groq_client(runtime_config)
    model  = get_groq_model(runtime_config)

    system = """You are a structured conversation analyst.
Given a chat transcript, return ONLY a valid JSON object with these exact keys:
{
  "original_query": "<first user message, verbatim>",
  "model_response": "<first assistant message, verbatim>",
  "intent_alignment": <float 0-1>,
  "constraint_score": <float 0-1>,
  "keyword_analysis": {
    "expected_keywords": [<list of strings>],
    "actual_keywords":   [<list of strings>]
  },
  "constraint_analysis": {
    "missing_constraints": [<list of strings>]
  }
}

Rules:
- intent_alignment: how well the model addressed the user's original goal
- constraint_score: fraction of user constraints the model respected
- expected_keywords: key terms the user implied or stated
- actual_keywords:   key terms the model actually used
- missing_constraints: specific requirements or conditions the model ignored
- Return ONLY JSON, no markdown, no explanation.
"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": conversation_text},
        ],
        temperature=0.1,
        max_tokens=600,
    )
    import json
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except Exception:
        return {}
