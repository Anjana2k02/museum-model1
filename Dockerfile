# ──────────────────────────────────────────────────────────────────
# HAR Realtime API — Production Docker Image
# Base: Python 3.11-slim (Debian-based, small footprint)
#
# The 48MB .joblib model is baked in for a self-contained deploy.
# Layer order: requirements → source → model (maximises cache hits)
# ──────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Disable .pyc files and enable real-time stdout/stderr (visible in `docker logs`)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install C/C++ build tools needed by numpy/scipy at compile time.
# Installed and removed in a single RUN layer to keep final image lean.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# ── Layer 1: Python dependencies (cached unless requirements.txt changes) ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Layer 2: Application source (cached unless code changes) ──
COPY api/        api/
COPY inference/  inference/
COPY main.py     main.py

# ── Layer 3: Pre-trained model (cached unless model is retrained) ──
COPY har_position_model.joblib har_position_model.joblib

# Set model path as an absolute path inside the container.
# Overrides the relative default in api/main.py so the model
# is always found regardless of working directory.
ENV HAR_MODEL_PATH=/app/har_position_model.joblib
ENV HAR_WINDOW_SIZE=128
ENV HAR_STEP_SIZE=10

# HOST and ENV are intentionally NOT set here.
# They are injected at `docker run` time via --env-file /opt/har-api/.env
# and the explicit -e HOST=0.0.0.0 -e ENV=live flags in the deploy script.

EXPOSE 8000

# Exec form (JSON array) — signals (SIGTERM) go directly to Python, not a shell.
# This enables graceful shutdown when `docker stop` is called.
CMD ["python", "main.py"]
