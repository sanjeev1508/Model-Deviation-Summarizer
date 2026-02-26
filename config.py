import os
from dotenv import load_dotenv

load_dotenv()

# ==============================
# OLLAMA CONFIG
# ==============================
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text:latest")

# ==============================
# NVIDIA / OPENAI CONFIG
# ==============================
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
