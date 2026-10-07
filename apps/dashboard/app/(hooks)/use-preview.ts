"use client";

import { useQuery } from "@tanstack/react-query";
import { QUERY_STALE_TIME } from "@/lib/constants";
import { QUERY_KEYS } from "@/lib/query-keys";
import { ApiPreviewRequest, ApiPreviewResponse } from "@fiery/types";
import { previewAction } from "../(actions)/volcano-action";

export function usePreview(args: ApiPreviewRequest | null) {
  const interferogramId = args?.interferogramId ?? null;
  const seismicEventId = args?.seismicEventId ?? null;
  const enabled =
    args != null && Boolean(interferogramId) !== Boolean(seismicEventId);
  return useQuery<ApiPreviewResponse | null>({
    queryKey: QUERY_KEYS.preview(interferogramId, seismicEventId),
    queryFn: () =>
      previewAction({
        interferogramId,
        seismicEventId,
      }),
    staleTime: QUERY_STALE_TIME,
    enabled,
  });
}
