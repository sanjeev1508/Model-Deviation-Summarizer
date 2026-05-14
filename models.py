from pydantic import BaseModel
from typing import List, Optional

import config as app_config


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    conversation: List[Message]

    domain: Optional[str] = "education"
    language: Optional[str] = "auto"

    # Embedding config (None = use server defaults from .env)
    embedding_model: Optional[str] = None

    # Legacy fields kept for backward compat
    embedding_provider: Optional[str] = None
    embedding_api_key: Optional[str] = None
    llm_type: Optional[str] = "groq"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None  # user-selected model from extension

    model_config = {"protected_namespaces": ()}

    def get_runtime_config(self) -> dict:
        prov = (self.embedding_provider or app_config.EMBEDDING_PROVIDER).strip().lower()
        em = self.embedding_model
        if em is None or em == "":
            em = (
                app_config.GROQ_EMBED_MODEL
                if prov == "groq"
                else app_config.EMBED_MODEL
            )
        return {
            "domain": self.domain,
            "language": self.language,
            "embedding_provider": prov,
            "embedding_model": em,
            "api_key": self.api_key,
            "model": self.model,  # extension-chosen LLM; may be None (falls back to .env)
        }


class IntegratedResponse(BaseModel):
    final_output: str
