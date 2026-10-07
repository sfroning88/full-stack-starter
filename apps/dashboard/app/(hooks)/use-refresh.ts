"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import posthog from "posthog-js";
import { QUERY_KEYS } from "@/lib/query-keys";
import {
  POSTHOG_EVENTS,
  ApiKeyRequest,
  ApiRefreshResponse,
} from "@fiery/types";
import { refreshAction } from "../(actions)/admin-action";

export function useRefresh(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (args: ApiKeyRequest): Promise<ApiRefreshResponse> =>
      refreshAction(args),
    onSuccess: async (data, args) => {
      posthog.capture(POSTHOG_EVENTS.refresh, {
        user_id: userId,
        artifact_id: data.artifactId,
        tier: data.tier,
        role: data.role,
        ready: data.ready,
      });
      await queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.artifact(args.tier, args.role),
      });
    },
  });
}
