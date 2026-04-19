"""
Embedding service using sentence-transformers.
No Ollama/OpenAI embedding API path is used.
"""
from sentence_transformers import SentenceTransformer
import numpy as np
import config as app_config

_model_cache: dict[str, SentenceTransformer] = {}


def _get_model(model_name: str | None = None) -> SentenceTransformer:
    name = model_name or app_config.EMBED_MODEL
    if name not in _model_cache:
        _model_cache[name] = SentenceTransformer(name)
    return _model_cache[name]


def embed_texts(texts: list[str], model_name: str | None = None) -> list[list[float]]:
    model = _get_model(model_name)
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom else 0.0
