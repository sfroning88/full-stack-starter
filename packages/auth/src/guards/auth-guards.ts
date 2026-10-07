import { cache } from "react";
import { redirect } from "next/navigation";
import { AppUserProfileNotFoundError, UserService } from "@fiery/services";
import { getSession } from "./session";
import { authRoutes } from "../routes";

export const requirePlatformAdmin = cache(
  async function requirePlatformAdmin() {
    const { supabaseUser } = await getSession();
    if (!supabaseUser) redirect(authRoutes.auth.login);
    let appUser;
    try {
      appUser = await UserService.ensureAppUserFromSupabaseAuth(supabaseUser);
    } catch (error) {
      if (error instanceof AppUserProfileNotFoundError) {
        redirect(authRoutes.noAccess);
      }
      throw error;
    }
    if (!appUser.isPlatformAdmin) {
      redirect(authRoutes.noAccess);
    }
    return {
      supabaseUser,
      appUser,
    };
  },
);

export const requireUser = cache(async function requireUser() {
  const { supabaseUser } = await getSession();
  if (!supabaseUser) redirect(authRoutes.auth.login);
  let appUser;
  try {
    appUser = await UserService.ensureAppUserFromSupabaseAuth(supabaseUser);
  } catch (error) {
    if (error instanceof AppUserProfileNotFoundError) {
      redirect(authRoutes.noAccess);
    }
    throw error;
  }
  return {
    supabaseUser,
    appUser,
  };
});
