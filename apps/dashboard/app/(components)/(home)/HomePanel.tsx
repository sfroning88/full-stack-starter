"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useMediaQuery } from "@/app/(hooks)/use-media-query";
import { useFetchVolcanoes } from "@/app/(hooks)/use-fetch-volcanoes";
import { useUserId } from "@/app/(hooks)/use-user-id";
import { MOBILE_BREAKPOINT, EMPTY_VOLCANOES } from "@/lib/constants";
import { TEST_IDS } from "@lib/test-ids";
import { VolcanoDashboard } from "@fiery/types";

const HomeMap = dynamic(() => import("./HomeMap").then((map) => map.HomeMap), {
  ssr: false,
  loading: () => <p className="text-white/50 text-sm">Loading map...</p>,
});

type HomePanelProps = {
  initialData?: VolcanoDashboard[];
};

export function HomePanel({ initialData }: HomePanelProps) {
  const userId = useUserId();
  const isMobile = !useMediaQuery(`(min-width: ${MOBILE_BREAKPOINT}px)`, true);

  const {
    data: volcanos,
    isLoading,
    isError,
    error,
  } = useFetchVolcanoes(userId, initialData);

  const [selectedId, setSelectedId] = useState<string | null>(null);

  const listed = volcanos ?? EMPTY_VOLCANOES;

  return (
    <div className="space-y-4 font-data">
      {isLoading ? (
        <p className="text-white/50 text-sm">Loading volcanoes…</p>
      ) : isError ? (
        <p className="text-red-400 text-sm">
          {error instanceof Error ? error.message : "Could not load volcanoes."}
        </p>
      ) : (
        <div
          data-testid={TEST_IDS.homeMap}
          className="h-[70vh] overflow-hidden border border-white/10 rounded-md bg-surface-dark"
        >
          <HomeMap
            userId={userId}
            volcanoes={listed}
            selectedId={selectedId}
            onSelect={setSelectedId}
            isMobile={isMobile}
          />
        </div>
      )}
    </div>
  );
}
