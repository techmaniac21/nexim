FROM python:3.11-slim

# Keep Python output unbuffered and avoid writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for audio playback and building some Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        build-essential \
        libffi-dev \
        libsodium-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./

# Upgrade pip and install Python dependencies
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/

# Create a small, non-root user (optional but recommended)
RUN useradd -m appuser || true
USER appuser

# Default command to run the bot
CMD ["python", "src/main.py"]
