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
# EMBEDDING CONFIG (Groq-friendly local embeddings)
# ==============================
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
