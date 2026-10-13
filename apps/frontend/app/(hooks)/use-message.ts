"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import posthog from "posthog-js";
import { QUERY_KEYS } from "@/lib/query-keys";
import { POSTHOG_EVENTS, type ApiJobsResponse } from "@my-project/types";
import { messageAction as homeMessageAction } from "../(actions)/home-action";
import { messageAction as adminMessageAction } from "../(actions)/admin-action";

export function useHomeMessage(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<ApiJobsResponse> =>
      homeMessageAction(undefined),
    onSuccess: async (data) => {
      posthog.capture(POSTHOG_EVENTS.home_messages_api, {
        user_id: userId,
        job_count: data.jobIds.length,
      });
      await queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.messages(userId),
      });
    },
  });
}

export function useAdminMessage(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<ApiJobsResponse> =>
      adminMessageAction(undefined),
    onSuccess: async (data) => {
      posthog.capture(POSTHOG_EVENTS.admin_messages_api, {
        user_id: userId,
        job_count: data.jobIds.length,
      });
      await queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.messages(userId),
      });
    },
  });
}
