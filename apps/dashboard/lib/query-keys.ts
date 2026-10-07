import { ModelTier, ModelRole, TrainingSampleSource } from "@fiery/types";

export const QUERY_KEYS = {
  user: (userId: string) => ["user", userId] as const,
  volcanoes: (userId: string) => ["volcanoes", userId] as const,
  volcano: (volcanoId: string) => ["volcano", volcanoId] as const,
  interferogram: (interferogramId: string) =>
    ["interferogram", interferogramId] as const,
  seismicEvent: (seismicEventId: string) =>
    ["seismicEvent", seismicEventId] as const,
  preview: (interferogramId: string | null, seismicEventId: string | null) =>
    [
      "preview",
      interferogramId ?? "(none)",
      seismicEventId ?? "(none)",
    ] as const,
  source: (source: TrainingSampleSource) => ["source", source] as const,
  version: (versionId: string) => ["version", versionId] as const,
  contract: (contractId: string) => ["contract", contractId] as const,
  session: (sessionId: string) => ["session", sessionId] as const,
  artifacts: (userId: string) => ["artifacts", userId] as const,
  winners: (userId: string) => ["winners", userId] as const,
  artifact: (tier: ModelTier, role: ModelRole) =>
    ["artifact", tier, role] as const,
};
