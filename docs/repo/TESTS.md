# Test Orchestration

Last updates: **October 2026**

## Playwright Testing

**[`Playwright`](https://playwright.dev/docs/ci)** enables us to run individual _`smoke tests`_:

- How interactive is the portal?
- Do URLs lead where they should?
- Are page elements reactive to input?

```env
VERCEL_AUTOMATION_BYPASS_SECRET=...
PLAYWRIGHT_BASE_URL=...
PLAYWRIGHT_EMAIL=...
PLAYWRIGHT_PASSWORD=...
```

All four staging user variables are required and wired up to a real **test user** from **Supabase `auth.users`**.

```md
/.github/workflows/
└── playwright.yml # github action

/apps/frontend/
├── e2e/
│ ├── global-setup.ts # playwright global instance
│ └── smoke.spec.ts # individual tests to run
└── playwright.config.ts # config class definition

/scripts/github/
├── post-playwright-comment.js # post summary
└── summarize-playwright-results.sh # fitler action output
```

Keep in mind:

- Do not **cross reference backend APIs** because that is an **integration risk**
- Every test is checking for **URL validity, element values, or user interactivity**

## Documentation

See these official articles and integration examples:

- [playwright.dev/docs/ci](https://playwright.dev/docs/ci)
- [playwright.dev/docs/best-practices](https://playwright.dev/docs/best-practices)
- [infinite-table.com/the-best-testing-setup-for-frontends-playwright-nextjs](https://infinite-table.com/blog/2024/04/18/the-best-testing-setup-for-frontends-playwright-nextjs)

## e2e Testing

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

## Unit Testing

**[`Pytest`](https://docs.pytest.org/en/stable/)** enables us to run individual _`unit_tests`_:

- Do functions behave as expected?
- Is syntax and object handling correct?

```md
apps/backend/tests/
├── conftest.py
└── unit/
└── test_domain.py
```

Keep in mind:

- Unit tests never touch the database, Redis, S3, or any third-party API (every boundary is mocked)
- Each `conftest.py` import modules exactly as the app does (`from integrations... import ...`)
- Each suite runs against its own `.venv`; a missing `.venv` counts as a failure (ie create one)
