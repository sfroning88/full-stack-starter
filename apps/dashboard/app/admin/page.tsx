import type { Metadata } from "next";
import { Suspense } from "react";
import Link from "next/link";
import { routes } from "@lib/routes";
import { TEST_IDS } from "@lib/test-ids";
import { requirePlatformAdmin } from "@fiery/auth/server";
import { ModelDashboard } from "@fiery/types";
import { fetchModelsCached } from "@/lib/api/cache/models-cache";
import { fetchWinnersCached } from "@/lib/api/cache/winners-cache";
import { AdminSkeleton } from "@/app/(components)/(admin)/AdminSkeleton";
import { AdminAsync } from "@/app/(components)/(admin)/AdminAsync";

export const metadata: Metadata = {
  title: "Admin",
  description: "Machine learning pipeline for Fiery Spirit models.",
  robots: { index: false, follow: false },
};

export default async function AdminPage() {
  const { supabaseUser } = await requirePlatformAdmin();
  const winnersPromise = fetchWinnersCached(supabaseUser.id).catch(
    (): ModelDashboard[] => [],
  );
  const modelsPromise = fetchModelsCached(supabaseUser.id).catch(
    (): ModelDashboard[] => [],
  );

  return (
    <div className="flex flex-col gap-6" data-testid={TEST_IDS.adminScreen}>
      <h1
        data-testid={TEST_IDS.modelsHeading}
        className="text-lg font-semibold text-fiery-crimson-400 sm:text-2xl"
      >
        Machine Learning Pipeline
      </h1>
      <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
        <Link
          href={routes.base.root}
          data-testid={TEST_IDS.backToDashboardLink}
          className="w-fit shrink-0 text-sm font-medium text-zinc-900 underline underline-offset-4 dark:text-zinc-100"
        >
          Back to dashboard
        </Link>
      </div>
      <Suspense fallback={<AdminSkeleton />}>
        <AdminAsync
          initialWinnersPromise={winnersPromise}
          initialModelsPromise={modelsPromise}
        />
      </Suspense>
    </div>
  );
}
