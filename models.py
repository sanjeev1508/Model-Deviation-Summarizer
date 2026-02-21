from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    conversation: List[Message]
    # Dynamic Configuration
    embedding_model: Optional[str] = "nomic-embed-text:latest"
    embedding_provider: Optional[str] = "local"
    embedding_api_key: Optional[str] = None
    llm_type: Optional[str] = "nvidia"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None

    model_config = {"protected_namespaces": ()}


class IntegratedResponse(BaseModel):
    final_output: str
