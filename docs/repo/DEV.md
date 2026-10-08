# Developer Setup

Last updated: **October 2026**

## Quickstart

To setup the env:

```bash
cp .env.example .env.local
cp .env.example .env.prod
pnpm use:[local|[prod]
pnpm use:link
```

To setup the container:

```bash
pnpm redis:up && pnpm db:up
pnpm db:prisma db push --accept-data-loss
pnpm redis:nuke && pnpm db:nuke # reset
```

To launch the frontend:

```sh
pnpm install
pnpm build
pnpm dev
```

To setup the venv:

```bash
pnpm check:python-venvs
```

To launch the backend:

```sh
cd apps/backend
source .venv/bin/activate
uvicorn src.main:app --port 8000
```

To launch the workers:

```bash
cd apps/backend
source .venv/bin/activate
python -m src.worker_runner
```
