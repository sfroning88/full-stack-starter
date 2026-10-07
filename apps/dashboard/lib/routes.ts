import { authRoutes } from "@fiery/auth/routes";

export const routes = {
  ...authRoutes,
  base: {
    root: "/" as const,
  },
  admin: {
    root: "/admin" as const,
  },
} as const;

export const publicAppPaths = [routes.base.root] as const;

export const adminAppPaths = [routes.admin.root];
