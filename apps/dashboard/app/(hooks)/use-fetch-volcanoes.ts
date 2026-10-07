"use client";

import { useQuery } from "@tanstack/react-query";
import { QUERY_STALE_TIME } from "@/lib/constants";
import { QUERY_KEYS } from "@/lib/query-keys";
import { VolcanoDashboard } from "@fiery/types";
import { fetchVolcanoesAction } from "../(actions)/volcano-action";

export function useFetchVolcanoes(
  userId: string | null,
  initialData?: VolcanoDashboard[],
) {
  return useQuery<VolcanoDashboard[]>({
    queryKey: QUERY_KEYS.volcanoes(userId || "public"),
    queryFn: () => fetchVolcanoesAction(),
    staleTime: QUERY_STALE_TIME,
    initialData,
  });
}
