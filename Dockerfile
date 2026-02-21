FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt update && apt install -y \
    curl \
    python3 \
    python3-pip \
    zstd \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Pull models during build (important)
RUN ollama pull llama3
RUN ollama pull nomic-embed-text

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt

EXPOSE 8000
EXPOSE 11434

CMD ollama serve & \
    sleep 5 && \
    uvicorn main:app --host 0.0.0.0 --port $PORT