import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from statistics import mean

from openai import OpenAI
from config import OLLAMA_BASE_URL, EMBED_MODEL, NVIDIA_API_KEY, BASE_URL, MODEL_NAME
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

# Download NLTK resources (quietly)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

def get_client(config=None):
    api_key = NVIDIA_API_KEY
    base_url = BASE_URL
    
    if config:
        if config.get("api_key"):
            api_key = config["api_key"]
        
        # Priority: explicit base_url > provider mapping
        if config.get("base_url"):
            base_url = config["base_url"]
        elif config.get("llm_type"):
            llm_type = config.get("llm_type").lower()
            if llm_type == "nvidia":
                base_url = "https://integrate.api.nvidia.com/v1"
            elif llm_type == "openai" or llm_type == "gpt":
                base_url = "https://api.openai.com/v1"
            elif llm_type == "gemini":
                base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            elif llm_type == "ollama" or llm_type == "local":
                 base_url = config.get("ollama_url") or OLLAMA_BASE_URL
                 if not base_url.endswith("/v1"):
                     base_url = base_url.rstrip("/") + "/v1"

    return OpenAI(
        api_key=api_key or "dummy", 
        base_url=base_url
    )

def get_model_name(config=None):
    if config and config.get("model_name"):
        return config["model_name"]
    return MODEL_NAME

# ==============================
# EMBEDDING
# ==============================

def preprocess_text(text: str) -> str:
    # 1. Tokenize
    tokens = word_tokenize(text.lower())
    # 2. Remove stopwords & stem
    processed_tokens = [
        stemmer.stem(word) 
        for word in tokens 
        if word.isalnum() and word not in stop_words
    ]
    return " ".join(processed_tokens)

def embed_text(text: str, config=None):
    # Preprocess before embedding to reduce noise and length
    clean_text = preprocess_text(text)
    if not clean_text:
        clean_text = text # Fallback if everything is removed

    embed_model = EMBED_MODEL
    provider = "local"
    api_key = None
    ollama_url = OLLAMA_BASE_URL
    
    if config:
        if config.get("embedding_model"):
            embed_model = config["embedding_model"]
        if config.get("embedding_provider"):
            provider = config["embedding_provider"]
        if config.get("embedding_api_key"):
            api_key = config["embedding_api_key"]
        if config.get("ollama_url"):
            ollama_url = config["ollama_url"]

    # API Logic
    if provider == "openai":
         client = OpenAI(api_key=api_key)
         response = client.embeddings.create(input=[clean_text], model=embed_model or "text-embedding-3-small")
         return np.array(response.data[0].embedding).reshape(1, -1)
    
    elif provider == "nvidia":
         # NVIDIA often uses OpenAI client format but different base URL
         client = OpenAI(
             api_key=api_key, 
             base_url="https://integrate.api.nvidia.com/v1"
         )
         response = client.embeddings.create(input=[clean_text], model=embed_model or "nvidia/nv-embed-v1")
         return np.array(response.data[0].embedding).reshape(1, -1)

    # Fallback / Local (Ollama)
    # Default to Ollama API
    try:
        response = requests.post(
            f"{ollama_url}/api/embeddings",
            json={"model": embed_model, "prompt": clean_text}
        )
        if response.status_code == 200:
             return np.array(response.json()["embedding"]).reshape(1, -1)
        else:
             print(f"Ollama Error: {response.text}")
             return np.zeros((1, 768)) # Fallback
    except Exception as e:
        print(f"Embedding Error: {e}")
        return np.zeros((1, 768))


def cosine(a, b):
    return float(cosine_similarity(a, b)[0][0])


# ==============================
# EXPECTATION INFERENCE
# ==============================

def infer_expectation(user_message: str, config=None):
    prompt = f"""
Abstract the following user message into a structured expectation description.
Return short structured description only.

User message:
{user_message}
"""
    client = get_client(config)
    model = get_model_name(config)
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return response.choices[0].message.content.strip()


# ==============================
# COMPLEXITY
# ==============================

def complexity_score(text: str):
    words = len(text.split())
    sentences = text.count(".") + text.count("?") + text.count("!")
    return words / (sentences + 1)


# ==============================
# TURN ANALYSIS
# ==============================

def analyze_turn(user_msg, model_msg, config=None):
    user_emb = embed_text(user_msg, config)
    model_emb = embed_text(model_msg, config)

    semantic_alignment = cosine(user_emb, model_emb)

    expectation_text = infer_expectation(user_msg, config)
    expectation_emb = embed_text(expectation_text, config)

    expectation_alignment = cosine(expectation_emb, model_emb)

    complexity_gap = abs(
        complexity_score(user_msg) - complexity_score(model_msg)
    )

    deviation_score = (
        (1 - semantic_alignment) * 0.4 +
        (1 - expectation_alignment) * 0.4 +
        (complexity_gap / 50) * 0.2
    )

    return {
        "semantic_alignment": semantic_alignment,
        "expectation_alignment": expectation_alignment,
        "complexity_gap": complexity_gap,
        "deviation_score": deviation_score
    }


# ==============================
# CONVERSATION ANALYSIS
# ==============================

def analyze_conversation(chat, config=None):

    conversation = chat["conversation"]
    pairs = []

    for i in range(len(conversation) - 1):
        if conversation[i]["role"] == "user" and conversation[i+1]["role"] == "model":
            pairs.append((conversation[i]["content"], conversation[i+1]["content"]))

    turn_results = []

    for user_msg, model_msg in pairs:
        turn_results.append(analyze_turn(user_msg, model_msg, config))

    avg_alignment = mean([r["semantic_alignment"] for r in turn_results])
    avg_expectation_alignment = mean([r["expectation_alignment"] for r in turn_results])
    avg_deviation = mean([r["deviation_score"] for r in turn_results])
    max_deviation = max([r["deviation_score"] for r in turn_results])

    deviation_trend = (
        "increasing"
        if turn_results[-1]["deviation_score"] > turn_results[0]["deviation_score"]
        else "stable/decreasing"
    )

    return {
        "turn_level_results": turn_results,
        "conversation_metrics": {
            "average_semantic_alignment": avg_alignment,
            "average_expectation_alignment": avg_expectation_alignment,
            "average_deviation_score": avg_deviation,
            "max_deviation_score": max_deviation,
            "deviation_trend": deviation_trend,
            "turn_count": len(turn_results)
        }
    }


# ==============================
# META SUMMARY
# ==============================

def summarize_conversation(features, config=None):

    prompt = f"""
Given the following structured conversation deviation metrics:

{features["conversation_metrics"]}

Classify:
1. Alignment Quality (Low/Medium/High)
2. User Frustration Probability (0-100)
3. Deviation Type
4. Conversation Stability
5. Risk Level (0-100)

Return JSON only.
"""
    client = get_client(config)
    model = get_model_name(config)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    return response.choices[0].message.content.strip()


def evaluate_deviations(conversation_text: str, config=None):
    prompt = f"""
Analyze the following conversation and extract two specific insights:
1. "deviated_into": A short summary of topics or directions the model took that were distractions or not what the user wanted.
2. "user_expectation": A clear, direct statement of what the user actually wants the model to do.

Conversation:
{conversation_text}

Return JSON with keys: "deviated_into", "user_expectation".
"""

    client = get_client(config)
    model = get_model_name(config)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    return response.choices[0].message.content.strip()
