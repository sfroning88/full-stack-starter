import "server-only";

import { cookies } from "next/headers";
import { USER_ID_COOKIE_NAME } from "@lib/constants";

export async function getUserIdFromCookies(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(USER_ID_COOKIE_NAME)?.value || null;
}
