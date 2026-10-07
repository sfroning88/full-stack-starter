"use server";

import { redirect } from "next/navigation";
import { revalidateTag } from "next/cache";
import { z } from "zod";
import { AuthService } from "@fiery/services";
import {
  SignInInput,
  SignInResult,
  SignOutResult,
  SignupFields,
  SignupResult,
} from "@fiery/types";
import { createPublicAction, selfUserAction } from "../guards/action-guards";
import { invalidateSessionCache } from "../guards/session";
import { supabaseServerClient } from "../client/server";
import { authRoutes } from "../routes";
import { AUTH_QUERY_KEYS, APP_ORIGIN } from "../constants";

const signInSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(5, "Password must be at least 5 characters"),
});

export const signInAction = createPublicAction(
  signInSchema,
  async ({ input }: { input: SignInInput }): Promise<SignInResult> => {
    const supabase = await supabaseServerClient();
    const result = await AuthService.signIn({
      email: input.email,
      password: input.password,
      supabaseClient: supabase,
    });
    if (!result.ok) return result;
    invalidateSessionCache();
    return { ok: true };
  },
);

const signOutSchema = z.object({});

export const signOutAction = selfUserAction(
  signOutSchema,
  async (): Promise<SignOutResult> => {
    const supabase = await supabaseServerClient();
    const result = await AuthService.signOut({
      supabaseClient: supabase,
    });
    if (!result.ok) return result;
    invalidateSessionCache();
    for (const tag of [...AUTH_QUERY_KEYS.currentUser]) revalidateTag(tag);
    revalidateTag("organizations");
    redirect(authRoutes.root);
  },
);

const signupSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  name: z.string().min(1, "Name is required"),
});

export const signupAction = createPublicAction(
  signupSchema,
  async ({ input }: { input: SignupFields }): Promise<SignupResult> => {
    const { email, password, name } = input;
    try {
      const supabase = await supabaseServerClient();
      const result = await AuthService.signup({
        fields: {
          email,
          password,
          name,
        },
        origin: APP_ORIGIN,
        supabaseClient: supabase,
      });
      if (!result.success) return result;
      invalidateSessionCache();
      return result;
    } catch (error) {
      return {
        success: false,
        error:
          error instanceof Error ? error.message : "Failed to create account",
        user: null,
      };
    }
  },
);
