import { unstable_cache } from "next/cache";
import { CACHE_STALE_TIME } from "@/lib/constants";
import { QUERY_KEYS } from "@/lib/query-keys";
import type { ModelDashboard } from "@fiery/types";
import { AdminService } from "@/lib/services";

const adminService = new AdminService();

export async function fetchModelsCached(
  userId: string,
): Promise<ModelDashboard[]> {
  return unstable_cache(
    async () => {
      return await adminService.fetchModels();
    },
    [...QUERY_KEYS.artifacts(userId)],
    {
      tags: [...QUERY_KEYS.artifacts(userId)],
      revalidate: CACHE_STALE_TIME,
    },
  )();
}
