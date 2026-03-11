# Hyper-Sentinel v2 — MarketAgent Dockerfile
# ============================================
# Multi-stage build following tobalo/gogent Dockerfile pattern.
# Stage 1: Install Python dependencies into a venv.
# Stage 2: Copy only the venv + source for a minimal runtime image.

# ─── Stage 1: Builder ──────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps for compiling Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create venv and install deps
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ─── Stage 2: Runtime ──────────────────────────────────────────
FROM python:3.12-slim

# Install runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (security: least privilege)
RUN useradd -r -s /bin/false -m sentinel

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data && chown -R sentinel:sentinel /app

# Switch to non-root user
USER sentinel

# Environment defaults
ENV NATS_URL="nats://nats:4222" \
    LLM_PROVIDER="CLAUDE" \
    LLM_MODEL="" \
    LLM_API_KEY="" \
    AGENT_NAME="MarketAgent" \
    DB_PATH="/app/data/agent_decisions.db" \
    LOG_LEVEL="INFO" \
    PYTHONUNBUFFERED="1"

# Health check — verify the process is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f "subscriber" || exit 1

# Entry point
ENTRYPOINT ["python", "subscriber.py"]
