"use client";

import { useQuery } from "@tanstack/react-query";
import { QUERY_STALE_TIME } from "@/lib/constants";
import { QUERY_KEYS } from "@/lib/query-keys";
import { getMyProfileAction } from "../(actions)/user-action";

export function useMyProfile(userId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.user(userId),
    queryFn: () => getMyProfileAction({}),
    staleTime: QUERY_STALE_TIME,
    enabled: !!userId,
  });
}
