# AI Coding Agents

## Workspace

`Turbo monorepo` using `pnpm` workspaces, which possibly includes:

- `Next.js` with `TypeScript` for **frontends** deployed to `Vercel`
- `FastAPI` with `Python` for **backends** deployed to `Render`
- `Supabase` with `PostgreSQL` for **database**
- `Prisma ORM` with `TypeScript` for **schema migrations**
- `Docker` with `Redis` + `Postgres` for **local development**
- `Environment variables` are managed at **root level** with `pnpm use:[local|dev|prod]`
- Each app has a **symbolically linked** environment to the root `.env`
- Shared packages for `TypeScript` files and config under `./packages/*` as `aliases`
- Shared package for `Python` files and config under `./packages/python` as `aliases`

## Rules

- Do not attempt to run `terminal commands` or `create test scripts`
- Use the **simplest possible iteration** while following the rules
- Match the existing **code syntax and style** while avoiding `in-line comments`
- Treat `Prisma ORM` as the **source of truth** under `./packages/db/prisma/schema`
- Additional **workflow documentation** exists under `./docs`
