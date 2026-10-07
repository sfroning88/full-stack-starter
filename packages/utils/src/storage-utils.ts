import { TrainingSampleSource } from "@fiery/types";

const SOURCE_PREFIXES = new Set<string>(Object.values(TrainingSampleSource));
const UNREFINED_KEY = /^([a-z]+)\/([0-9a-f]{64})\.npz$/;

export function isBlobStorageArtifact(value: unknown): boolean {
  if (typeof value !== "string") return false;
  const trimmed = value.trim();
  if (!trimmed || trimmed.includes("\\") || trimmed.includes(".."))
    return false;
  const match = UNREFINED_KEY.exec(trimmed);
  if (!match) return false;
  return SOURCE_PREFIXES.has(match[1]);
}
