import type { User as SupabaseUser } from "@supabase/supabase-js";
import type { User as PrismaUser } from "@fiery/db";

export type SessionProfile = {
  supabaseUser: SupabaseUser | null;
};

export type CurrentUser = PrismaUser;

export type SignInInput = {
  email: string;
  password: string;
};

export type SignInResult = { ok: true } | { ok: false; error: string };

export type SignOutResult = { ok: true } | { ok: false; error: string };

export type SignupFields = {
  email: string;
  password: string;
  name: string;
};

export type SignupResult = {
  success: boolean;
  error: string | null;
  user: string | null;
};
