import "server-only";

import { env } from "@fiery/config";
import { createServerClient, type CookieMethodsServer } from "@supabase/ssr";
import { cookies } from "next/headers";
import type { SupabaseSSRServerOptions } from "./ssr";

export async function supabaseServerClient() {
  if (!env.NEXT_PUBLIC_SUPABASE_URL) {
    throw new Error("NEXT_PUBLIC_SUPABASE_URL environment variable is not set");
  }
  if (!env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
    throw new Error(
      "NEXT_PUBLIC_SUPABASE_ANON_KEY environment variable is not set",
    );
  }
  const cookieStore = await cookies();
  const cookieMethods: CookieMethodsServer = {
    getAll() {
      return cookieStore.getAll();
    },
    setAll(cookiesToSet) {
      cookiesToSet.forEach(({ name, value, options }) => {
        cookieStore.set(name, value, options);
      });
    },
  };
  const options: SupabaseSSRServerOptions = {
    cookies: cookieMethods,
  };
  return createServerClient(
    env.NEXT_PUBLIC_SUPABASE_URL,
    env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    options,
  );
}
