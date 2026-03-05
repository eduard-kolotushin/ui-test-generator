ARG PYTHON_IMAGE=python:3.13-slim
FROM ${PYTHON_IMAGE}

LABEL org.opencontainers.image.source="ui-test-generator"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System dependencies: build tools, git, curl, Node.js + npm for deep-agents-ui.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        ca-certificates \
        pkg-config \
        libssl-dev \
        nodejs \
        npm && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml README.md langgraph.json ./
COPY src ./src
COPY wheels ./wheels

# Install Python dependencies (project + langgraph-cli)
RUN pip install --upgrade pip && \
    pip install .

# Clone and install Deep Agents UI
RUN git clone https://github.com/langchain-ai/deep-agents-ui.git && \
    cd deep-agents-ui && \
    npm install

# Expose LangGraph dev API and Deep Agents UI ports
EXPOSE 2024 3000

# Default model selection and Postgres-backed store/checkpointer.
# Override these at runtime as needed.
ENV LLM_MODEL="GigaChat-2" \
    HUB_BASE_URL="" \
    HUB_API_KEY="sk-local" \
    POSTGRES_CHECKPOINT_URL="postgresql://user:pass@postgres:5432/checkpoints?sslmode=disable" \
    POSTGRES_STORE_URL="postgresql://user:pass@postgres:5432/store?sslmode=disable"

# Start LangGraph dev server and Deep Agents UI in the same container.
# - LangGraph dev will listen on :2024
# - Deep Agents UI will listen on :3000
CMD bash -lc "langgraph dev & cd deep-agents-ui && npm run dev -- --host 0.0.0.0 --port 3000"

