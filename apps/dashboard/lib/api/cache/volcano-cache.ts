import { unstable_cache } from "next/cache";
import { CACHE_STALE_TIME } from "@/lib/constants";
import { QUERY_KEYS } from "@/lib/query-keys";
import type { VolcanoDashboard } from "@fiery/types";
import { VolcanoService } from "@/lib/services";

const volcanoService = new VolcanoService();

export async function fetchVolcanoesCached(
  userId: string | null,
): Promise<VolcanoDashboard[]> {
  return unstable_cache(
    async () => {
      return await volcanoService.fetchVolcanoes();
    },
    [...QUERY_KEYS.volcanoes(userId || "public")],
    {
      tags: [...QUERY_KEYS.volcanoes(userId || "public")],
      revalidate: CACHE_STALE_TIME,
    },
  )();
}
