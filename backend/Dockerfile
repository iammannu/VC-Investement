FROM python:3.12-slim AS base

WORKDIR /app

# System deps for PDF processing and OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libpango-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright chromium for JS-rendered pages
RUN playwright install chromium --with-deps 2>/dev/null || true

# ── Development stage ──────────────────────────────────────
FROM base AS development

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Production stage ───────────────────────────────────────
FROM base AS production

COPY . .

RUN addgroup --system appgroup && adduser --system --group appuser
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
