FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

COPY apps /app/apps
COPY db /app/db
COPY worker /app/worker

ENV PYTHONPATH=/app
CMD ["python", "-m", "worker.main", "--poll"]
