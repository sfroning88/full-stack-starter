# Vercel Supabase Connection

Last updated: **August 2026**

## Overview

Vercel uses IPv6 by default; Supabase requires IPv4. Connection automatically uses pgBouncer pooling and IPv4-first DNS resolution.

## Environment Variables

```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
DIRECT_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
```

Both URLs required. `DATABASE_URL` used for queries; `DIRECT_URL` used for migrations and introspection.

## Connection Handling

`getModifiedDatabaseUrl()` automatically modifies `DATABASE_URL` for Supabase:

- Adds `pgbouncer=true`
- Sets `connection_limit=5`
- Sets `pool_timeout=20`
- Sets `statement_timeout=15s`
- Sets `pooler_mode=transaction`

Prisma schema uses both URLs:

```prisma
datasource db {
  provider   = "postgresql"
  url        = env("DATABASE_URL")
  directUrl  = env("DIRECT_URL")
}
```

## DNS Resolution

If DNS errors occur, set:

```env
NODE_OPTIONS=--dns-result-order=ipv4first
```

For direct IP connection:

```env
DB_USE_IP=true
DB_IP_ADDRESS=123.45.67.89
```
