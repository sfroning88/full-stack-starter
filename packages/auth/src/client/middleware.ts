import { env } from "@fiery/config";
import { createServerClient, type CookieMethodsServer } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { authRoutes } from "../routes";
import type { SupabaseSSRServerOptions } from "./ssr";

function isPublicPath(pathname: string): boolean {
  if (pathname === "/") return true;
  if (pathname.startsWith("/auth")) return true;
  if (pathname.startsWith("/no-access")) return true;
  if (pathname.startsWith("/unauthorized")) return true;
  if (pathname.startsWith("/_next")) return true;
  if (pathname.startsWith("/favicon")) return true;
  return false;
}

function requiresAuthentication(pathname: string): boolean {
  if (isPublicPath(pathname)) return false;
  return pathname.startsWith("/admin");
}

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  });
  const cookieMethods: CookieMethodsServer = {
    getAll() {
      return request.cookies.getAll();
    },
    setAll(cookiesToSet) {
      cookiesToSet.forEach(({ name, value }) => {
        request.cookies.set(name, value);
      });
      supabaseResponse = NextResponse.next({
        request,
      });
      cookiesToSet.forEach(({ name, value, options }) => {
        supabaseResponse.cookies.set(name, value, options);
      });
    },
  };
  const options: SupabaseSSRServerOptions = {
    cookies: cookieMethods,
  };
  const supabase = createServerClient(
    env.NEXT_PUBLIC_SUPABASE_URL!,
    env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    options,
  );
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const { pathname } = request.nextUrl;
  if (!user && requiresAuthentication(pathname)) {
    const url = request.nextUrl.clone();
    url.pathname = authRoutes.auth.login;
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }
  return supabaseResponse;
}
