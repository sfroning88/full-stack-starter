# Postgres Database

Connection and schema is managed by [`@fiery/db`](packages/db):

- `Prisma v7` + `PostgreSQL v17.6` installations
- Config and migrations live under [`packages/db`](packages/db)
- [`prisma.config.ts`](packges/db/prisma.config.ts) points to `prisma/`
- CLI uses **`DIRECT_URL`** to run `prisma/migrations`
- Apps use **`DATABASE_URL`** to manage a _pooled connection_

Supabase **Auth** manages _security and IAM_:

- Database profiles stored as **`auth.users`**
- App profiles stored as **`iam.users`**
- `UUID` fields must match to create link
- Trigger [`on_auth_user_created`](packages/db/prisma/migrations/20260414000000_on_auth_user_created/migration.sql)

Developers can manage the database by:

- `pnpm db:generate` to regenerate the client
- `pnpm db:migrate <migration_name>` creates `.sql`
- `pnpm db:deploy` applies pending migrations
- `pnpm run db:prisma <prisma-args>` runs Prisma CLI
- _Do not run `pnpm prisma` bare from root_
