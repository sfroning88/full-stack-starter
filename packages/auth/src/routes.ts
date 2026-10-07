export const authRoutes = {
  root: "/" as const,
  noAccess: "/no-access" as const,
  unauthorized: "/unauthorized" as const,
  auth: {
    login: "/auth/login" as const,
    verify: "/auth/verify" as const,
    callback: "/auth/callback" as const,
  },
} as const;

export type AuthRoutes = typeof authRoutes;
