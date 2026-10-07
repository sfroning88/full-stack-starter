import "server-only";

import { cache } from "react";
import { revalidatePath } from "next/cache";
import { supabaseServerClient } from "../client/server";
import { SessionProfile } from "@fiery/types";

export const getSession = cache(async (): Promise<SessionProfile> => {
  const supabase = await supabaseServerClient();
  const { data, error } = await supabase.auth.getUser();
  if (error || !data.user) {
    return { supabaseUser: null };
  }
  return {
    supabaseUser: data.user,
  };
});

export async function invalidateSessionCache() {
  revalidatePath("/", "layout");
}
