# ---- base ----
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

# ---- deps ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- app ----
COPY . .

# Render (and most PaaS hosts) inject a PORT env var and route traffic to it.
# Default to 8000 so `docker run -p 8000:8000` still works locally.
ENV PORT=8000
EXPOSE 8000

# NOTE: the HEALTHCHECK uses $PORT too, so it stays correct on any host.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/health" || exit 1

# Shell form so ${PORT} is expanded at runtime by the container's shell.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
