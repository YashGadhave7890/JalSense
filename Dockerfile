# =============================================================================
# JalSense: Production Multi-Service Container Image
# Python 3.11 Slim Base
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Ensure non-interactive installs and unbuffered console logging
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OS utilities (curl for health probes, build essentials)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source repository
COPY . .

# Expose FastAPI backend (8000) and Streamlit dashboard (8501)
EXPOSE 8000 8501

# Healthcheck for FastAPI service
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default entrypoint starts the FastAPI REST service
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
