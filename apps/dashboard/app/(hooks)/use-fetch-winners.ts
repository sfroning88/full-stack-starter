"use client";

import { useQuery } from "@tanstack/react-query";
import { QUERY_STALE_TIME } from "@/lib/constants";
import { QUERY_KEYS } from "@/lib/query-keys";
import { ModelDashboard } from "@fiery/types";
import { fetchWinnersAction } from "../(actions)/admin-action";

export function useFetchWinners(
  userId: string,
  initialWinners?: ModelDashboard[],
) {
  return useQuery<ModelDashboard[]>({
    queryKey: QUERY_KEYS.winners(userId),
    queryFn: () => fetchWinnersAction(),
    staleTime: QUERY_STALE_TIME,
    enabled: !!userId,
    initialData: initialWinners,
  });
}
