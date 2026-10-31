# syntax=docker/dockerfile:1.7
#
# Build from the repository root:
#   docker build -f docker/Dockerfile -t ai-resume-mining .
#
# Build arguments
#   TORCH_INDEX_URL  wheel index for torch (CPU by default; use
#                    https://download.pytorch.org/whl/cu124 for NVIDIA GPUs)
#   WITH_LLAMA_CPP   install llama-cpp-python (compiled from source, slow);
#                    needed for LLM_PROVIDER=llama_cpp
#   WITH_OCR         install Tesseract (English and Vietnamese) so scanned
#                    PDFs can be read when OCR_ENABLED=true
ARG PYTHON_VERSION=3.11


# ---------------------------------------------------------------- builder
FROM python:${PYTHON_VERSION}-slim AS builder

ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
ARG WITH_LLAMA_CPP=true

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

COPY requirements.txt requirements-llama.txt ./

# torch first, from its own index, so the large CUDA wheels are not pulled
# from PyPI; the pinned version is read from requirements.txt.
RUN grep '^torch==' requirements.txt \
        | xargs pip install --index-url "${TORCH_INDEX_URL}" \
    && pip install -r requirements.txt

# Separate step so toggling WITH_LLAMA_CPP does not reinstall everything above.
RUN if [ "${WITH_LLAMA_CPP}" = "true" ]; then \
      pip install -r requirements-llama.txt; \
    fi


# ---------------------------------------------------------------- runtime
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/home/appuser/.cache/huggingface

ARG WITH_OCR=false

# libgomp1: OpenMP runtime used by FAISS, torch and llama.cpp.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && if [ "${WITH_OCR}" = "true" ]; then \
         apt-get install -y --no-install-recommends \
           tesseract-ocr tesseract-ocr-eng tesseract-ocr-vie; \
       fi \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 10001 appuser \
    && useradd --system --uid 10001 --gid appuser --create-home appuser

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

COPY app/ app/

# Operational scripts (index reindex / consistency check).
COPY scripts/reindex_candidates.py scripts/check_index_consistency.py scripts/

# Reference data the API reads at runtime. Uploads, the FAISS index and
# models are not part of the image; compose mounts them as volumes.
COPY data/dictionaries/ data/dictionaries/
COPY data/skills/ data/skills/
COPY data/taxonomy/generated/ data/taxonomy/generated/
COPY data/esco/processed/ data/esco/processed/

RUN mkdir -p data/uploads faiss_index logs models "${HF_HOME}" \
    && chown -R appuser:appuser /app /home/appuser

USER appuser

EXPOSE 8000

# One process on purpose: the FAISS index and model singletons live in
# process memory, so do not add --workers.
HEALTHCHECK --interval=30s --timeout=5s --start-period=420s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
