import { type ReactNode } from "react";
import { requirePlatformAdmin } from "@my-project/auth/server";

export default async function AdminLayout({
  children,
}: {
  children: ReactNode;
}) {
  await requirePlatformAdmin();
  return (
    <div className="min-h-screen bg-amber-50 dark:bg-zinc-950">
      <div className="mx-auto max-w-3xl px-6 py-8">{children}</div>
    </div>
  );
}
