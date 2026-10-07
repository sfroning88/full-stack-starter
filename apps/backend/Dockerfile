FROM python:3.13-slim

WORKDIR /repo/apps/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY packages/python /repo/packages/python
COPY apps/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV HF_HUB_DISABLE_XET=1
ENV HF_HOME=/root/.cache/huggingface

RUN python -c "\
from huggingface_hub import hf_hub_download; \
hf_hub_download(repo_id='timm/vit_small_patch16_224.augreg_in21k_ft_in1k', \
filename='model.safetensors', \
revision='7e2c55630205e1266030f18370f4c6ed1a514b52') \
"

COPY apps/backend/ .
RUN chmod +x scripts/start.sh

CMD ["./scripts/start.sh"]
