import type { NextRequest } from "next/server";
import { COOKIE_MAX_AGE, USER_ID_COOKIE_NAME } from "@lib/constants";
import { generateAnonymousUserId } from "@lib/utils/src/middleware-utils";
import { updateSession } from "@fiery/auth/middleware";

export async function middleware(request: NextRequest) {
  const response = await updateSession(request);
  if (!request.cookies.get(USER_ID_COOKIE_NAME)?.value) {
    response.cookies.set(USER_ID_COOKIE_NAME, generateAnonymousUserId(), {
      maxAge: COOKIE_MAX_AGE,
      path: "/",
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
    });
  }
  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
