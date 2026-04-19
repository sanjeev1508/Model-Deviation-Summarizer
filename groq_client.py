"""
Central Groq client factory.
Uses fixed api_key and model from config.
"""
from groq import Groq
import config as app_config


def get_groq_client(runtime_config: dict | None = None) -> Groq:
    rc = runtime_config or {}
    api_key = rc.get("api_key") or app_config.GROQ_API_KEY
    if not api_key:
        raise ValueError("Groq API key not set. Enter it in the extension or set GROQ_API_KEY in .env.")
    return Groq(api_key=api_key)


def get_groq_model(runtime_config: dict | None = None) -> str:
    rc = runtime_config or {}
    return rc.get("model") or app_config.GROQ_MODEL


def get_domain(runtime_config: dict | None = None) -> str:
    return (runtime_config or {}).get("domain") or app_config.DOMAIN
