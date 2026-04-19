from pydantic import BaseModel
from typing import List, Optional


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    conversation: List[Message]

    domain: Optional[str] = "education"
    language: Optional[str] = "auto"

    # Embedding config
    embedding_model: Optional[str] = "all-MiniLM-L6-v2"

    # Legacy fields kept for backward compat
    embedding_provider: Optional[str] = "local"
    embedding_api_key: Optional[str] = None
    llm_type: Optional[str] = "groq"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None  # user-selected model from extension

    model_config = {"protected_namespaces": ()}

    def get_runtime_config(self) -> dict:
        return {
            "domain": self.domain,
            "language": self.language,
            "embedding_model": self.embedding_model,
            "api_key": self.api_key,
            "model": self.model,  # extension-chosen LLM; may be None (falls back to .env)
        }


class IntegratedResponse(BaseModel):
    final_output: str
