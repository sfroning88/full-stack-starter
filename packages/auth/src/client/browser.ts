import { createBrowserClient } from "@supabase/ssr";
import { env } from "@fiery/config";
import { authRoutes } from "../routes";

const supabaseUrl = env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export function supabaseClient() {
  return createBrowserClient(supabaseUrl!, supabaseAnonKey!);
}

export async function hardResetSupabaseConnection() {
  if (typeof window === "undefined") {
    return;
  }
  try {
    const browserClient = supabaseClient();
    await browserClient.auth.signOut();
    document.cookie.split(";").forEach((cookie) => {
      const eqPos = cookie.indexOf("=");
      const name =
        eqPos > -1 ? cookie.substring(0, eqPos).trim() : cookie.trim();
      if (name.includes("supabase") || name.startsWith("sb-")) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
      }
    });
    Object.keys(localStorage).forEach((key) => {
      if (key.includes("supabase") || key.includes("sb-")) {
        localStorage.removeItem(key);
      }
    });
    Object.keys(sessionStorage).forEach((key) => {
      if (key.includes("supabase") || key.includes("sb-")) {
        sessionStorage.removeItem(key);
      }
    });
    window.location.href = authRoutes.auth.login;
  } catch {
    window.location.href = authRoutes.auth.login;
  }
}

export async function clearAllSupabaseSessions() {
  if (typeof window === "undefined") {
    return;
  }
  try {
    const browserClient = supabaseClient();
    await browserClient.auth.signOut();
    Object.keys(localStorage).forEach((key) => {
      if (key.includes("supabase") || key.includes("sb-")) {
        localStorage.removeItem(key);
      }
    });
    Object.keys(sessionStorage).forEach((key) => {
      if (key.includes("supabase") || key.includes("sb-")) {
        sessionStorage.removeItem(key);
      }
    });
  } catch {
    // nothing
  }
}

export async function checkSupabaseHealth() {
  try {
    const browserClient = supabaseClient();
    const { error } = await browserClient.auth.getSession();
    if (error) throw error;
    return true;
  } catch {
    return false;
  }
}
