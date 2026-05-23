FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

COPY services/nlp_pipeline/requirements.txt .

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install everything in one pass using the PyTorch CPU index.
# Listing torch first ensures the CPU wheel is resolved before
# sentence-transformers can pull in the GPU variant.
RUN pip install \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Install spacy small English model
RUN pip install \
    https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["python", "-m", "uvicorn", "services.nlp_pipeline.main:app", "--host", "0.0.0.0", "--port", "8003"]
