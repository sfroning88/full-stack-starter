import { NextResponse } from "next/server";
import { supabaseServerClient } from "@my-project/auth/server";
import { authRoutes } from "@my-project/auth/routes";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const nextParam = searchParams.get("next") ?? authRoutes.root;
  const next =
    nextParam.startsWith("/") && !nextParam.startsWith("//")
      ? nextParam
      : authRoutes.root;
  if (code) {
    const supabase = await supabaseServerClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }
  return NextResponse.redirect(`${origin}${authRoutes.auth.login}`);
}
