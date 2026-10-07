# Playwright CI

Last updated: **August 2026**

## Overview

CI pipeline of **github actions** uses **[`playwright`](https://playwright.dev/docs/ci)**.
This enables us to run individual _`smoke tests`_ that target basic functionalities:

- How interactive is the portal?
- Do URLs lead where they should?
- Are page elements reactive to input?

## Environment Variables

```env
VERCEL_AUTOMATION_BYPASS_SECRET=...
PLAYWRIGHT_BASE_URL=...
PLAYWRIGHT_EMAIL=...
PLAYWRIGHT_PASSWORD=...
```

All four staging user variables are required and wired up to a real **test user** from **Supabase `auth.users`**.

## Structure

```md
/.github/workflows/
└── playwright.yml # github action

/apps/[app]/
├── e2e/
│ ├── global-setup.ts # playwright global instance
│ └── smoke.spec.ts # individual tests to run
└── playwright.config.ts # config class definition

/scripts/
├── post-playwright-comment.js # post summary
└── summarize-playwright-results.sh # fitler action output
```

When building out new functionality, add individual _`smoke tests`_ to the specs file.

## Caveats

Keep in mind:

- Do not **cross reference backend APIs** because that is an **integration risk**
- Every test is checking for **URL validity, element values, or user interactivity**

## Documentation

See these official articles and integration examples:

- [playwright.dev/docs/ci](https://playwright.dev/docs/ci)
- [playwright.dev/docs/best-practices](https://playwright.dev/docs/best-practices)
- [infinite-table.com/the-best-testing-setup-for-frontends-playwright-nextjs](https://infinite-table.com/blog/2024/04/18/the-best-testing-setup-for-frontends-playwright-nextjs)
