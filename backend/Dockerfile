# ── Backend Dockerfile ──────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm

WORKDIR /app

# install system deps for psycopg and sentence-transformers
RUN apt-clean || true && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get update -y --fix-missing && \
    apt-get install -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy application source
COPY . .

# create uploads directory
RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
