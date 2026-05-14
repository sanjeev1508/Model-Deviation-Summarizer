import os
from dotenv import load_dotenv

load_dotenv()

# ==============================
# GROQ CONFIG (primary LLM)
# ==============================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

# ==============================
# DOMAIN CONFIG
# ==============================
DOMAIN = os.getenv("DOMAIN", "education")  # education | healthcare | banking

# ==============================
# LANGUAGE CONFIG
# ==============================
SUPPORTED_LANGUAGES = ["en", "ta", "hi"]  # English, Tamil, Hindi
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

# ==============================
# EMBEDDING CONFIG
# groq = HTTP embeddings at api.groq.com (default, no PyTorch on server)
# local = sentence-transformers (see requirements-local-embed.txt)
# ==============================
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "groq").strip().lower()
_raw_embed = os.getenv("GROQ_EMBED_MODEL", "nomic-embed-text-v1_5").strip()
# Groq OpenAPI id uses underscore (v1_5); "v1.5" in env or docs causes HTTP 400 schema errors.
if _raw_embed.startswith("nomic-embed-text-v1") and "v1_5" not in _raw_embed:
    _raw_embed = "nomic-embed-text-v1_5"
GROQ_EMBED_MODEL = _raw_embed
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
