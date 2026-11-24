# Bangkok CCTV Image Analysis — one image for pipeline, scrapers, notebooks and dashboard
# Build:  docker compose build
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    YOLO_CONFIG_DIR=/tmp/ultralytics

# System libraries: OpenCV (libgl1, libglib2.0-0), building wheels, curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libgl1 libglib2.0-0 curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only PyTorch first, so ultralytics doesn't pull the multi-GB CUDA build.
# (Docker on macOS has no GPU access anyway — run heavy YOLO jobs on Colab/GPU if needed.)
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision

# Python dependencies (cached layer: only rebuilds when requirements.txt changes).
# The trailing "-e ." line is installed later, after the source is copied.
COPY requirements.txt .
RUN grep -v '^-e' requirements.txt > /tmp/requirements.txt \
    && pip install -r /tmp/requirements.txt

# Chromium + its OS dependencies for Playwright scrapers
RUN playwright install --with-deps chromium

# Project source, installed in editable mode (src/bkk_cctv)
COPY . .
RUN pip install --no-deps -e .

EXPOSE 8501 8888
CMD ["bash"]
