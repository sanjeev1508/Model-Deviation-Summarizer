"""Shared analysis helpers used by FastAPI (main.py) and Appwrite (main_appwrite.py)."""


def build_master_payload(features: dict, kc_data: dict) -> dict:
    """Assemble the JSON object passed to MASTER_PROMPT (generate_master_report)."""
    agg = features.get("aggregate", {})
    return {
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
