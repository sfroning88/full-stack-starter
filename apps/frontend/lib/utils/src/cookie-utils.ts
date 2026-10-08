import { COOKIE_MAX_AGE, USER_ID_COOKIE_NAME } from "@lib/constants";

function generateUserId(): string {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join(
    "",
  );
}

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop()?.split(";").shift() || null;
  }
  return null;
}

export function setCookie(name: string, value: string, maxAge: number): void {
  if (typeof document === "undefined") return;
  const isSecure = window.location.protocol === "https:";
  const secureFlag = isSecure ? "; Secure" : "";
  document.cookie = `${name}=${value}; max-age=${maxAge}; path=/; SameSite=None${secureFlag}`;
}

export function getOrCreateUserId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const stored = getCookie(USER_ID_COOKIE_NAME);
  if (stored) {
    return stored;
  }
  const newUserId = generateUserId();
  setCookie(USER_ID_COOKIE_NAME, newUserId, COOKIE_MAX_AGE);
  return newUserId;
}

export function createUserIdCookie(userId: string, maxAge: number): string {
  const secureFlag = process.env.NODE_ENV === "production" ? "; Secure" : "";
  return `${USER_ID_COOKIE_NAME}=${userId}; Max-Age=${maxAge}; Path=/; SameSite=Lax${secureFlag}`;
}
