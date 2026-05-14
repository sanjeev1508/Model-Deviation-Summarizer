"""
Embeddings: Groq OpenAI-compatible HTTP API by default (no PyTorch on server).

Optional local path: EMBEDDING_PROVIDER=local + sentence-transformers
(see requirements-local-embed.txt).

If Groq returns model_not_found for all Nomic embedding ids (some keys/regions
have no embedding access), optional fallback uses local SentenceTransformers
when installed (EMBEDDING_GROQ_FALLBACK_LOCAL=true, default).
"""
from __future__ import annotations

import math
from typing import Any

import httpx

import config as app_config

GROQ_EMBEDDINGS_URL = "https://api.groq.com/openai/v1/embeddings"
_MAX_BATCH = 48

_NOMIC_IDS = ("nomic-embed-text-v1.5", "nomic-embed-text-v1_5")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity; L2-normalizes inputs defensively (Groq vs ST)."""
    def _norm(v: list[float]) -> list[float]:
        m = math.sqrt(sum(x * x for x in v))
        return [x / m for x in v] if m else v

    na, nb = _norm(a), _norm(b)
    return float(sum(x * y for x, y in zip(na, nb)))


def _groq_embed_batches(texts: list[str], api_key: str, model: str) -> list[list[float]]:
    if not texts:
        return []
    api_key = api_key.strip()
    safe = [(t if t.strip() else " ") for t in texts]
    out: list[list[float]] = []
    with httpx.Client(timeout=120.0) as client:
        for i in range(0, len(safe), _MAX_BATCH):
            chunk = safe[i : i + _MAX_BATCH]
            resp = client.post(
                GROQ_EMBEDDINGS_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "input": chunk,
                    "encoding_format": "float",
                },
            )
            detail: Any
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Groq embeddings HTTP {resp.status_code} (model={model!r}): {detail}"
                ) from None
            data = sorted(detail["data"], key=lambda d: d["index"])
            out.extend([d["embedding"] for d in data])
    return out


def _groq_model_missing(err: RuntimeError) -> bool:
    s = str(err).lower()
    return "model_not_found" in s or "does not exist" in s or "do not have access" in s


def _groq_nomic_candidates(primary: str) -> list[str]:
    """Always try v1.5 (dot) first, then v1_5 — order does not depend on primary spelling."""
    p = (primary or "").strip().lower()
    if "nomic" in p and "embed" in p:
        return list(_NOMIC_IDS)
    if not p:
        return list(_NOMIC_IDS)
    return [primary.strip()]


def _groq_embed_with_fallback(texts: list[str], api_key: str, primary: str) -> list[list[float]]:
    candidates = _groq_nomic_candidates(primary)
    last: RuntimeError | None = None
    for i, m in enumerate(candidates):
        try:
            return _groq_embed_batches(texts, api_key, m)
        except RuntimeError as e:
            last = e
            if i < len(candidates) - 1 and _groq_model_missing(e):
                continue
            raise
    assert last is not None
    raise last


def _try_local_sentence_transformers(texts: list[str]) -> list[list[float]] | None:
    try:
        from embedding_local import embed_texts_local
    except ImportError:
        return None
    return embed_texts_local(texts, app_config.EMBED_MODEL)


def _resolve_groq_model(rc: dict) -> str:
    m = (rc.get("embedding_model") or app_config.GROQ_EMBED_MODEL or "").strip()
    if not m or "MiniLM" in m or m.startswith("sentence-"):
        m = app_config.GROQ_EMBED_MODEL
    if m in ("nomic-embed-text-v1_5", "nomic-embed-text-v1-5"):
        m = "nomic-embed-text-v1.5"
    return m


def embed_texts(texts: list[str], runtime_config: dict | None = None) -> list[list[float]]:
    """
    Batch-embed texts. Provider from runtime_config or EMBEDDING_PROVIDER env.
    Groq path requires api_key in runtime_config or GROQ_API_KEY in env.
    """
    rc = runtime_config or {}
    provider = (rc.get("embedding_provider") or app_config.EMBEDDING_PROVIDER).lower().strip()
    api_key = rc.get("api_key") or app_config.GROQ_API_KEY

    if provider == "groq":
        if not api_key:
            raise ValueError(
                "Groq API key required for embedding_provider=groq "
                "(Authorization header on /analyze or GROQ_API_KEY in .env)."
            )
        model = _resolve_groq_model(rc)
        try:
            return _groq_embed_with_fallback(texts, api_key, model)
        except RuntimeError as e:
            if not app_config.EMBEDDING_GROQ_FALLBACK_LOCAL or not _groq_model_missing(e):
                raise
            local_vec = _try_local_sentence_transformers(texts)
            if local_vec is None:
                raise RuntimeError(
                    "Groq Cloud rejected all Nomic embedding model ids (embeddings may be disabled "
                    "for this API key). Install local embeddings: pip install -r requirements-local-embed.txt "
                    "then set EMBEDDING_PROVIDER=local in .env, or keep EMBEDDING_GROQ_FALLBACK_LOCAL=true "
                    "after installing those packages."
                ) from e
            return local_vec

    if provider == "local":
        try:
            from embedding_local import embed_texts_local
        except ImportError as e:
            raise ImportError(
                "Local embeddings need sentence-transformers. "
                "pip install -r requirements-local-embed.txt"
            ) from e
        return embed_texts_local(texts, rc.get("embedding_model") or app_config.EMBED_MODEL)

    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {provider!r} (use groq or local)")
