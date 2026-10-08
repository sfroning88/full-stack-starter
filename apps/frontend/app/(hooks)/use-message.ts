"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/query-keys";
import { type ApiJobsResponse } from "@my-project/types";
import { messageAction as homeMessageAction } from "../(actions)/home-action";
import { messageAction as adminMessageAction } from "../(actions)/admin-action";

export function useHomeMessage(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<ApiJobsResponse> =>
      homeMessageAction(undefined),
    onSuccess: async () => {
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
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.messages(userId),
      });
    },
  });
}
