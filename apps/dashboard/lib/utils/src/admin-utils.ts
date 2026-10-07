import { TrainingSampleSource } from "@fiery/types";

export function coerceIngestSource(
  source: TrainingSampleSource,
): TrainingSampleSource {
  switch (source) {
    case TrainingSampleSource.hephaestus:
    case TrainingSampleSource.okada:
    case TrainingSampleSource.llaima:
      return source;
    default:
      return TrainingSampleSource.hephaestus;
  }
}
