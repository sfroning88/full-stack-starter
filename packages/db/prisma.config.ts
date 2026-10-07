import "dotenv/config";
import process from "node:process";
import { defineConfig } from "prisma/config";

/**
 * CLI (migrate, introspect, studio) uses a direct Postgres URL — not the pooled Supabase URL.
 * `prisma generate` does not connect; a placeholder is fine when DIRECT_URL is unset (e.g. CI).
 */
const directUrl =
  process.env.DIRECT_URL ??
  "postgresql://postgres:postgres@127.0.0.1:5432/postgres";

export default defineConfig({
  schema: "prisma/schema",
  migrations: {
    path: "prisma/migrations",
  },
  datasource: {
    url: directUrl,
  },
});
