# Base image
FROM ubuntu:22.04

# Install dependencies
RUN apt update && apt install -y \
    curl \
    python3 \
    python3-pip \
    zstd \
    ca-certificates

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working dir
WORKDIR /app

# Copy project
COPY . .

# Install Python deps
RUN pip3 install -r requirements.txt

# Expose ports
EXPOSE 8000
EXPOSE 11434

# Start both Ollama + FastAPI
CMD ollama serve & \
    sleep 5 && \
    uvicorn main:app --host 0.0.0.0 --port 8000