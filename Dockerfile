# AgentCore Runtime runs on Graviton, so the image must be ARM64.
FROM --platform=linux/arm64 python:3.12-slim AS builder
# HOME=/app puts Chroma's embedding model cache inside /app so it ships in the image.
ENV HOME=/app ANONYMIZED_TELEMETRY=False
WORKDIR /app
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agent/ agent/
COPY app.py .
# Build the product vector index (and download the embedding model) at build time.
RUN python -m agent.index_products

FROM --platform=linux/arm64 python:3.12-slim
RUN useradd -r -u 1001 -d /app appuser
WORKDIR /app
ENV HOME=/app PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 ANONYMIZED_TELEMETRY=False
COPY --from=builder --chown=appuser /app /app
USER appuser
EXPOSE 8080
# Binds to 0.0.0.0 for AgentCore internal routing. Not exposed directly to the internet.
CMD ["python", "app.py"]
