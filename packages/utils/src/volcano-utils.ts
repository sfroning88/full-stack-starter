import { VolcanoDashboard, VolcanoDashboardRow } from "@fiery/types";
import { isBlobStorageArtifact } from "./storage-utils";

export function toVolcanoDashboard(row: VolcanoDashboardRow): VolcanoDashboard {
  const interferogram =
    row.interferograms.find((sample) =>
      isBlobStorageArtifact(sample.storagePath),
    ) ?? null;
  const deformationInference = interferogram?.inferences[0] ?? null;
  const seismicEvent =
    row.seismicEvents.find((sample) =>
      isBlobStorageArtifact(sample.waveformPath),
    ) ?? null;
  const cloudInference =
    seismicEvent?.inferences.find(
      (infer) =>
        infer.artifact.promoted &&
        infer.artifact.tier === "cloud" &&
        infer.artifact.role === "teacher",
    ) ?? null;
  const edgeInference =
    seismicEvent?.inferences.find(
      (infer) =>
        infer.artifact.promoted &&
        infer.artifact.tier === "edge" &&
        infer.artifact.role === "student",
    ) ?? null;
  return {
    ...row,
    currentActivity: row.activities[0] ?? null,
    deformation: {
      sample: interferogram,
      inference: deformationInference,
      feedback: deformationInference?.feedback[0] ?? null,
      artifact: deformationInference?.artifact ?? null,
    },
    seismic: {
      sample: seismicEvent,
      cloud: {
        sample: null,
        inference: cloudInference,
        feedback: cloudInference?.feedback[0] ?? null,
        artifact: cloudInference?.artifact ?? null,
      },
      edge: {
        sample: null,
        inference: edgeInference,
        feedback: edgeInference?.feedback[0] ?? null,
        artifact: edgeInference?.artifact ?? null,
      },
    },
    _count: row._count,
  };
}
