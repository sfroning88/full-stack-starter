import type { Metadata } from "next";
import { Suspense } from "react";
import Link from "next/link";
import { routes } from "@lib/routes";
import { TEST_IDS } from "@lib/test-ids";
import { requirePlatformAdmin } from "@my-project/auth/server";
import { type MyClass } from "@my-project/types";
import { fetchMessagesCached } from "@/lib/api/cache/admin-cache";
import { AdminSkeleton } from "@/app/(components)/(admin)/AdminSkeleton";
import { AdminAsync } from "@/app/(components)/(admin)/AdminAsync";

export const metadata: Metadata = {
  title: "Admin",
  description: "MyProject admin — backend message demo.",
  robots: { index: false, follow: false },
};

export default async function AdminPage() {
  const { supabaseUser } = await requirePlatformAdmin();
  const messagesPromise = fetchMessagesCached(supabaseUser.id).catch(
    (): MyClass[] => [],
  );

  return (
    <div className="flex flex-col gap-6" data-testid={TEST_IDS.adminScreen}>
      <h1
        data-testid={TEST_IDS.adminMessagesHeading}
        className="text-lg font-semibold text-myproject-black sm:text-2xl"
      >
        Admin
      </h1>
      <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
        <Link
          href={routes.base.root}
          data-testid={TEST_IDS.backTofrontendLink}
          className="w-fit shrink-0 text-sm font-medium text-zinc-900 underline underline-offset-4 dark:text-zinc-100"
        >
          Back to frontend
        </Link>
      </div>
      <Suspense fallback={<AdminSkeleton />}>
        <AdminAsync initialMessagesPromise={messagesPromise} />
      </Suspense>
    </div>
  );
}
