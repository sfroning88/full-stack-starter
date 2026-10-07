import { PrismaPg } from "@prisma/adapter-pg";
import { setDefaultResultOrder } from "node:dns";
import { Prisma, PrismaClient } from "../prisma/src/generated/prisma";

// Prefer IPv4 when resolving Supabase hostnames (avoids some local/CI IPv6 issues).
setDefaultResultOrder("ipv4first");

/**
 * Recursively convert Prisma.Decimal instances to plain numbers so query
 * results are JSON-safe and can cross the Next.js Server → Client boundary.
 */
function convertDecimals(obj: unknown): unknown {
  if (obj === null || obj === undefined) return obj;
  if (obj instanceof Prisma.Decimal) return obj.toNumber();
  if (obj instanceof Date) return obj;
  if (Array.isArray(obj)) return obj.map(convertDecimals);
  if (typeof obj === "object") {
    return Object.fromEntries(
      Object.entries(obj).map(([k, v]) => [k, convertDecimals(v)]),
    );
  }
  return obj;
}

const globalForPrisma = globalThis as unknown as {
  prisma: ReturnType<typeof createClient> | undefined;
};

/**
 * Runtime: pooled URL (e.g. Supabase :6543 + pgbouncer). CLI uses DIRECT_URL from prisma.config.ts.
 * @see https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/databases-connections
 */
function createClient() {
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error("DATABASE_URL is not set");
  }
  return new PrismaClient({
    adapter: new PrismaPg({ connectionString: databaseUrl }),
    log: process.env.NODE_ENV === "development" ? ["error", "warn"] : ["error"],
  }).$extends({
    query: {
      $allModels: {
        async $allOperations({ args, query }) {
          const result = await query(args);
          return convertDecimals(result);
        },
      },
    },
  });
}

export const db = globalForPrisma.prisma ?? createClient();

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = db;
}
