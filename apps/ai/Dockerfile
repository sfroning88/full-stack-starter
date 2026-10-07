FROM python:3.13-slim

WORKDIR /repo/apps/ai

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY packages/python /repo/packages/python
COPY apps/ai/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/ai/ .
RUN chmod +x scripts/start.sh

CMD ["./scripts/start.sh"]
