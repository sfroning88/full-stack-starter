import "server-only";

import { db } from "@fiery/db";
import type { User } from "@fiery/db";
import type { User as SupabaseAuthUser } from "@supabase/supabase-js";

export class AppUserProfileNotFoundError extends Error {
  constructor(readonly supabaseUserId: string) {
    super(
      `No iam.users profile for Supabase user ${supabaseUserId}; expected DB trigger handle_new_user to create it.`,
    );
    this.name = "AppUserProfileNotFoundError";
  }
}

export const UserService = {
  async ensureAppUserFromSupabaseAuth(
    authUser: SupabaseAuthUser,
  ): Promise<User> {
    const appUser = await db.user.findUnique({
      where: { id: authUser.id },
    });
    if (!appUser) {
      throw new AppUserProfileNotFoundError(authUser.id);
    }
    return appUser;
  },
};
