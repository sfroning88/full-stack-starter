import { dateLikeToMs } from "@fiery/utils";
import {
  VolcanoDashboard,
  TrainingSignal,
  TrainingDeformationLabel,
  TrainingSeismicLabel,
  ModelTier,
  ModelRole,
  ApiInferenceRequest,
  InferenceLatest,
  InferenceOutcome,
  InferenceFeedbackDraft,
  InferenceModalView,
} from "@fiery/types";

export function inferenceRequest(
  volcano: VolcanoDashboard,
  signal: TrainingSignal,
): ApiInferenceRequest | null {
  if (signal === TrainingSignal.deformation) {
    const sample = volcano.deformation.sample;
    if (!sample) return null;
    const artifact = volcano.deformation.artifact;
    return {
      tier: artifact?.tier ?? ModelTier.cloud,
      role: artifact?.role ?? ModelRole.screener,
      interferogramId: sample.id,
      seismicEventId: null,
      volcanoId: volcano.id,
    };
  }
  const sample = volcano.seismic.sample;
  if (!sample) return null;
  const artifact =
    volcano.seismic.cloud.artifact ?? volcano.seismic.edge.artifact;
  return {
    tier: artifact?.tier ?? ModelTier.cloud,
    role: artifact?.role ?? ModelRole.teacher,
    interferogramId: null,
    seismicEventId: sample.id,
    volcanoId: volcano.id,
  };
}

export function latestSignalInference(
  volcano: VolcanoDashboard,
  signal: TrainingSignal,
): InferenceLatest | null {
  if (signal === TrainingSignal.deformation) {
    if (!volcano.deformation.inference) return null;
    return {
      kind: "deformation",
      inference: volcano.deformation.inference,
      feedback: volcano.deformation.feedback,
    };
  }
  const candidates: InferenceLatest[] = [];
  if (volcano.seismic.cloud.inference) {
    candidates.push({
      kind: "seismic",
      inference: volcano.seismic.cloud.inference,
      feedback: volcano.seismic.cloud.feedback,
    });
  }
  if (volcano.seismic.edge.inference) {
    candidates.push({
      kind: "seismic",
      inference: volcano.seismic.edge.inference,
      feedback: volcano.seismic.edge.feedback,
    });
  }
  return candidates.reduce<InferenceLatest | null>((best, next) => {
    if (!best) return next;
    return dateLikeToMs(next.inference.inferredAt) >
      dateLikeToMs(best.inference.inferredAt)
      ? next
      : best;
  }, null);
}

export function inferenceModalView(args: {
  signal: TrainingSignal;
  latest: InferenceLatest | null;
  served: InferenceOutcome | null;
  form: InferenceFeedbackDraft;
  feedbackSucceeded: boolean;
}): InferenceModalView {
  const { signal, latest, served, form, feedbackSucceeded } = args;
  const isDeformation = signal === TrainingSignal.deformation;
  const isSeismic = signal === TrainingSignal.seismic;
  const usingServed = served != null;
  const existingFeedback = latest?.feedback ?? null;
  const existingLabel = latest?.inference.label ?? null;
  const existingScore =
    latest?.kind === "deformation" ? latest.inference.score : null;
  const servedDeformation =
    usingServed && isDeformation
      ? (served.label as TrainingDeformationLabel | null)
      : null;
  const servedSeismic =
    usingServed && isSeismic
      ? (served.label as TrainingSeismicLabel | null)
      : null;

  return {
    label: served?.label ?? existingLabel,
    score: served?.score ?? existingScore,
    abstained: served?.abstained ?? latest?.inference.abstained ?? false,
    abstainedReason:
      served?.abstained_reason ?? latest?.inference.abstainedReason ?? null,
    artifactId: served?.artifact_id ?? latest?.inference.artifactId ?? null,
    hasResult: served != null || latest != null,
    submittedAgreed: usingServed
      ? form.agreed
      : (form.agreed ?? existingFeedback?.agreed ?? null),
    submittedCorrectedDeformation:
      form.correctedDeformation ??
      (usingServed
        ? servedDeformation
        : (existingFeedback?.correctedDeformation ??
          (latest?.kind === "deformation" ? latest.inference.label : null))),
    submittedCorrectedSeismic:
      form.correctedSeismic ??
      (usingServed
        ? servedSeismic
        : (existingFeedback?.correctedSeismic ??
          (latest?.kind === "seismic" ? latest.inference.label : null))),
    submittedNotes: usingServed
      ? form.notes
      : (form.notes ?? existingFeedback?.note ?? null),
    hasSubmitted: usingServed
      ? feedbackSucceeded
      : existingFeedback?.agreed != null || feedbackSucceeded,
  };
}
