"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import posthog from "posthog-js";
import { QUERY_KEYS } from "@/lib/query-keys";
import {
  POSTHOG_EVENTS,
  TrainingDeformationLabel,
  TrainingSeismicLabel,
} from "@fiery/types";
import { feedbackAction } from "../(actions)/volcano-action";

type FeedbackArgs = {
  agreed: boolean;
  correctedDeformation: TrainingDeformationLabel | null;
  correctedSeismic: TrainingSeismicLabel | null;
  note: string | null;
  volcanoId: string | null;
  interferogramId: string | null;
  seismicEventId: string | null;
  artifactId: string;
};

export function useFeedback(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (args: FeedbackArgs): Promise<void> => feedbackAction(args),
    onSuccess: async (_data, args) => {
      posthog.capture(POSTHOG_EVENTS.feedback, {
        user_id: userId,
        volcano_id: args.volcanoId,
        interferogram_id: args.interferogramId,
        seismic_event_id: args.seismicEventId,
        artifact_id: args.artifactId,
        corrected_deformation: args.correctedDeformation,
        corrected_seismic: args.correctedSeismic,
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
