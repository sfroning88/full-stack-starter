import type { CookieMethodsServer, CookieOptionsWithName } from "@supabase/ssr";

export type SupabaseSSRServerOptions = {
  cookies: CookieMethodsServer;
  cookieOptions?: CookieOptionsWithName;
  cookieEncoding?: "raw" | "base64url";
};
