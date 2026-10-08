# Test Orchestration

Last updates: **October 2026**

## e2e

```md
packages/python/src/tests/
├── orchestrator.py
├── endpoints.py
├── helpers.py
├── container.py
├── presets/
└── scripts/
```

All integration tests run through a single orchestrator at `packages/python`. The orchestrator spawns local `uvicorn` + `rq` processes per worker domain, seeds the local database, runs the selected workflow, then tears everything down.

```bash
cd packages/python
python -m src.e2e.orchestrator [**kwarg]
```

**Setup (local only):**

1. Start Docker Desktop
2. `pnpm use:local`
3. `pnpm redis:setup`
4. `pnpm db:setup`
5. `pnpm prisma db push --accept-data-loss`
6. `cd packages/python`
7. Activate venv: `python3 -m venv .venv && source .venv/bin/activate && pip install -e .`
8. `python -m src.e2e.orchestrator [train|predict]`

**Teardown:** `pnpm redis:nuke && pnpm db:nuke`

## Unit

```md
apps/\*\*/tests/
├── conftest.py
└── unit/
└── test_domain.py
```

```bash
cd apps/extract
.venv/bin/python -m pytest tests/ -q
```

```md
packages/python/src/tests/
├── conftest.py
└── unit/
└── test_domain.py
```

```bash
cd packages/python
.venv/bin/python -m pytest src/tests/unit -q
```

Unit tests are pure and isolated. They never touch the database, Redis, S3, or any third-party API — every boundary is mocked. Each `conftest.py` puts the app's `src/` on `sys.path` so tests import modules exactly as the app does (`from integrations... import ...`), and exposes shared fixtures.

Run all unit tests in sequence or individually:

```sh
./scripts/dev/python-unit-tests.sh [ai|backend|packages|all]
```

Each suite runs against its own `.venv`. A missing venv counts as a failure (run `./scripts/dev/setup-python-venvs.sh` first). The script exits non-zero if any requested suite fails.
