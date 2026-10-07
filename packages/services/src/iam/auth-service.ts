import "server-only";

import { db } from "@fiery/db";
import type { SupabaseClient } from "@supabase/supabase-js";
import {
  SignInResult,
  SignOutResult,
  SignupFields,
  SignupResult,
  CurrentUser,
} from "@fiery/types";
import { validateSignupFields } from "@fiery/utils";

export const AuthService = {
  async signIn(params: {
    email: string;
    password: string;
    supabaseClient: SupabaseClient;
  }): Promise<SignInResult> {
    const { error } = await params.supabaseClient.auth.signInWithPassword({
      email: params.email,
      password: params.password,
    });
    if (error) {
      return { ok: false, error: "Invalid email or password" };
    }
    return { ok: true };
  },

  async signOut(params: {
    supabaseClient: SupabaseClient;
  }): Promise<SignOutResult> {
    const { error } = await params.supabaseClient.auth.signOut();
    if (error) return { ok: false, error: error.message };
    return { ok: true };
  },

  async signup(params: {
    fields: SignupFields;
    origin: string;
    supabaseClient: SupabaseClient;
  }): Promise<SignupResult> {
    const { email, password, name } = params.fields;
    const validation = validateSignupFields(email, password, name);
    if (!validation.success) return validation;
    const { error, data } = await params.supabaseClient.auth.signUp({
      email,
      password,
      options: {
        data: { name },
        emailRedirectTo: `${params.origin}/auth/callback`,
      },
    });
    if (error) {
      return {
        success: false,
        error: error.message,
        user: null,
      };
    }
    if (!data?.user) {
      return {
        success: false,
        error: "Failed to create auth.user",
        user: null,
      };
    }
    try {
      if (!data.user.email) {
        throw new Error("Failed to create user in database");
      }
      const dbUser = await db.user.upsert({
        where: { id: data.user.id },
        update: {
          isActive: true,
          name: name,
        },
        create: {
          id: data.user.id,
          email: data.user.email,
          phone: null,
          name: name,
          isActive: true,
          isPlatformAdmin: false,
        },
      });
      if (!dbUser || !dbUser.id) {
        throw new Error("Failed to create user in database");
      }
    } catch {
      throw new Error("Failed to create user in database");
    }
    return {
      success: true,
      error: null,
      user: data.user.email || "",
    };
  },

  async fetchCurrentUser(userId: string): Promise<CurrentUser | null> {
    return db.user.findUnique({
      where: { id: userId },
    });
  },
};
