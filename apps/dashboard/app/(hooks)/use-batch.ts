"use client";

import { useMutation } from "@tanstack/react-query";
import posthog from "posthog-js";
import { POSTHOG_EVENTS, ApiKeyRequest, ApiJobsResponse } from "@fiery/types";
import { batchAction } from "../(actions)/admin-action";

export function useBatch(userId: string) {
  return useMutation({
    mutationFn: async (args: ApiKeyRequest): Promise<ApiJobsResponse> =>
      batchAction(args),
    onSuccess: async (data, args) => {
      posthog.capture(POSTHOG_EVENTS.batch, {
        user_id: userId,
        job_count: data.jobIds.length,
        tier: args.tier,
        role: args.role,
      });
    },
  });
}
