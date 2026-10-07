"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import posthog from "posthog-js";
import { QUERY_KEYS } from "@/lib/query-keys";
import {
  POSTHOG_EVENTS,
  ApiIngestRequest,
  ApiJobsResponse,
} from "@fiery/types";
import { ingestAction } from "../(actions)/admin-action";

export function useIngest(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (args: ApiIngestRequest): Promise<ApiJobsResponse> =>
      ingestAction(args),
    onSuccess: async (data, args) => {
      posthog.capture(POSTHOG_EVENTS.ingest, {
        user_id: userId,
        job_count: data.jobIds.length,
      });
      await queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.source(args.source),
      });
    },
  });
}
