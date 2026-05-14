"""
Optional local embeddings via sentence-transformers (heavy deps).
Install: pip install -r requirements-local-embed.txt
Use: set EMBEDDING_PROVIDER=local in .env
"""
from sentence_transformers import SentenceTransformer
import config as app_config

_model_cache: dict[str, SentenceTransformer] = {}


def _get_model(model_name: str | None = None) -> SentenceTransformer:
    name = model_name or app_config.EMBED_MODEL
    if name not in _model_cache:
        _model_cache[name] = SentenceTransformer(name)
    return _model_cache[name]


def embed_texts_local(texts: list[str], model_name: str | None = None) -> list[list[float]]:
    model = _get_model(model_name)
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()
