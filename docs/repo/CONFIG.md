# Python Config

Last updated: **September 2026**

## Shared Python package

Cross-worker infrastructure lives in **`packages/python`** as **`fiery_python`**.
The app pins it via **`-e ../../packages/python`** in `requirements.in` / `requirements.txt`.
Use it for config, database pool, structured logging, Redis/RQ queue helpers, shared enums, shared utils, and FastAPI helpers.
App-only wiring stays under **`src/core/`**, **`src/main.py`** composes FastAPI with `fiery_python` and those modules.

## Deployment

The **`Dockerfile`** expects the **repository root** as build context.
**`WORKDIR`** is **`/repo/apps/[fastapi-app]`**.
Render **`buildFilter`** paths include **`packages/python/**`.

## Routes

Conventions:

- **`APIRouter`** with **`prefix`**; auth via **`Depends(dependency.get_token_header)`** from **`fiery_python`**
- Request and response models from **`integrations/*/schemas`**
- **`response_model`** on route decorators where appropriate
- **`observability`** with both `third_party_sentry` and `first_party_logging`
- - `bind_context` on (`correlation_id`, `path`) for request traces
- - `bind_job_context` (`SENTRY_JOB_CONTEXT_TAG_KEYS`) for multi-tenant traces

Raise HTTP errors with **`error(...)`** on (`application_error_type`).
Register handlers once in **`main.py`** with **`exception.register_exception_handlers(app)`**.

Routes are globally **rate limited** using [`slowapi`](https://github.com/laurentS/slowapi).

## Services

Import shared infrastructure from **`fiery_python`**, not from a local **`core`** package for those concerns.

Patterns:

- **`queue.enqueue_jobs(jobs)`** for batch enqueue (each job: func, args, optional job_id, job_timeout, tags, metadata, …)
- Optional dependencies: if something required for a route is missing, respond with **`error(..., status_code=503)`** (or appropriate code)

## Access Patterns

- Default queue name: **`predictions-default`**
- **`queue.get_connection()`** — Redis
- **`queue.enqueue_jobs(jobs)`** — batch enqueue
- **`SharedUtils`** — schema helpers from **`fiery_python`**

## Libraries

This application uses lightweight and free `libraries`:

- `Tailwind colors` -- see official documentation at [tailwindcss.com/docs/colors](https://tailwindcss.com/docs/colors)
- `Lucide React` -- see the official documentation at [lucide.dev/icons/](https://lucide.dev/icons/)
- `React Icons` -- see the official documentation at [react-icons.github.io/react-icons/](https://react-icons.github.io/react-icons/)
- `Sonner Toast` -- see the official documentation at [ui.shadcn.com/docs/components/radix/sonner](https://ui.shadcn.com/docs/components/radix/sonner)
