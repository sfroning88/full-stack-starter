"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import posthog from "posthog-js";
import { QUERY_KEYS } from "@/lib/query-keys";
import {
  POSTHOG_EVENTS,
  ApiRefineRequest,
  ApiRefineResponse,
} from "@fiery/types";
import { refineAction } from "../(actions)/admin-action";

export function useRefine(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (args: ApiRefineRequest): Promise<ApiRefineResponse> =>
      refineAction(args),
    onSuccess: async (data, args) => {
      posthog.capture(POSTHOG_EVENTS.ingest, {
        user_id: userId,
        job_count: data.jobIds.length,
        version_id: data.versionId,
        cached: data.cached,
      });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.contract(args.contractId),
        }),
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.version(data.versionId),
        }),
      ]);
    },
  });
}
