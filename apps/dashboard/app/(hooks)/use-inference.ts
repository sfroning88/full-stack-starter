"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import posthog from "posthog-js";
import { QUERY_KEYS } from "@/lib/query-keys";
import {
  POSTHOG_EVENTS,
  ApiInferenceRequest,
  ApiInferenceResponse,
} from "@fiery/types";
import { inferenceAction } from "../(actions)/volcano-action";

export function useInference(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (
      args: ApiInferenceRequest,
    ): Promise<ApiInferenceResponse | null> => inferenceAction(args),
    onSuccess: async (data, args) => {
      posthog.capture(POSTHOG_EVENTS.inference, {
        user_id: userId,
        volcano_id: args.volcanoId,
        interferogram_id: args.interferogramId,
        seismic_event_id: args.seismicEventId,
        probabilities: data?.result.probabilities,
        label: data?.result.label,
        score: data?.result.score,
        abstained: data?.result.abstained,
        abstained_reason: data?.result.abstained_reason,
      });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.volcanoes(userId),
        }),
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.volcano(args.volcanoId ?? "(none)"),
        }),
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.interferogram(args.interferogramId ?? "(none)"),
        }),
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.seismicEvent(args.seismicEventId ?? "(none)"),
        }),
      ]);
    },
  });
}
