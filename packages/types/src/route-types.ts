type ParamNames<S extends string> =
  S extends `${string}:${infer P}/${infer Rest}`
    ? P | ParamNames<`/${Rest}`>
    : S extends `${string}:${infer P}`
      ? P
      : never;

export type PathParams<T extends string> =
  ParamNames<T> extends never
    ? Record<never, never>
    : { [K in ParamNames<T>]: string | number };

type BuildRoute<T extends string> =
  ParamNames<T> extends never
    ? (() => string) & { template: T }
    : ((params: PathParams<T>) => string) & { template: T };

export function encodeSegment(v: string | number) {
  return encodeURIComponent(String(v));
}

function escapeRegex(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function createRoute<T extends string>(template: T): BuildRoute<T> {
  const builder = ((params?: Record<string, string | number>) => {
    let path = template as string;
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        path = path.replace(
          new RegExp(`:${escapeRegex(k)}(?=/|$)`),
          encodeSegment(v),
        );
      }
    }
    if (path.includes(":")) {
      throw new Error(`Missing path params for route "${template}"`);
    }
    return path;
  }) as BuildRoute<T>;
  return Object.assign(builder, { template }) as BuildRoute<T>;
}

export const IAM_ROUTES = {
  currentUser: createRoute("/api/auth/current-user"),
};

export type iamRoutes = (typeof IAM_ROUTES)[keyof typeof IAM_ROUTES];

export function base64UrlDecodeToUtf8(str: string): string {
  const base64 = str.replace(/-/g, "+").replace(/_/g, "/");
  const padded =
    base64.length % 4 === 0
      ? base64
      : base64 + "=".repeat(4 - (base64.length % 4));
  try {
    const binary = atob(padded);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return new TextDecoder().decode(bytes);
  } catch {
    throw new Error("Invalid base64 input in base64UrlDecodeToUtf8");
  }
}

export function safeRedirectPath(next: string | null, fallback = "/"): string {
  if (!next || typeof next !== "string") {
    return fallback;
  }
  const trimmed = next.trim();
  if (trimmed.includes("\\")) {
    return fallback;
  }
  if (trimmed.startsWith("/") && !trimmed.startsWith("//")) {
    return trimmed;
  }
  return fallback;
}
