"use client";

import { useQuery } from "@tanstack/react-query";
import { QUERY_STALE_TIME } from "@/lib/constants";
import { QUERY_KEYS } from "@/lib/query-keys";
import { type MyClass } from "@my-project/types";
import { fetchMessagesAction as fetchHomeMessagesAction } from "../(actions)/home-action";
import { fetchMessagesAction as fetchAdminMessagesAction } from "../(actions)/admin-action";

export function useFetchHomeMessages(
  userId: string,
  initialMessages?: MyClass[],
) {
  return useQuery<MyClass[]>({
    queryKey: QUERY_KEYS.messages(userId),
    queryFn: () => fetchHomeMessagesAction(undefined),
    staleTime: QUERY_STALE_TIME,
    initialData: initialMessages,
  });
}

export function useFetchAdminMessages(
  userId: string,
  initialMessages?: MyClass[],
) {
  return useQuery<MyClass[]>({
    queryKey: QUERY_KEYS.messages(userId),
    queryFn: () => fetchAdminMessagesAction(undefined),
    staleTime: QUERY_STALE_TIME,
    enabled: !!userId,
    initialData: initialMessages,
  });
}
