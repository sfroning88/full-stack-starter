"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import posthog from "posthog-js";
import { QUERY_KEYS } from "@/lib/query-keys";
import {
  POSTHOG_EVENTS,
  ApiTrainRequest,
  ApiTrainResponse,
} from "@fiery/types";
import { trainAction } from "../(actions)/admin-action";

export function useTrain(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (args: ApiTrainRequest): Promise<ApiTrainResponse> =>
      trainAction(args),
    onSuccess: async (data, args) => {
      posthog.capture(POSTHOG_EVENTS.train, {
        user_id: userId,
        job_count: data.jobIds.length,
        contractId: args.contractId,
        versionId: args.versionId,
        sessionId: data.sessionId,
        cached: data.cached,
      });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.contract(args.contractId),
        }),
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.version(args.versionId),
        }),
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.session(data.sessionId),
        }),
      ]);
    },
  });
}
