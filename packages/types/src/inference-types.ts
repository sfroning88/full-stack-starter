import { InferenceAbstainReason } from "@fiery/db/enums";
import type {
  InferenceDeformation as PrismaInferenceDeformation,
  InferenceSeismic as PrismaInferenceSeismic,
  InferenceFeedback as PrismaInferenceFeedback,
} from "@fiery/db";
import {
  TrainingDeformationLabel,
  TrainingSeismicLabel,
} from "./training-types";

export { InferenceAbstainReason };

export type InferenceDeformation = PrismaInferenceDeformation;
export type InferenceSeismic = PrismaInferenceSeismic;
export type InferenceFeedback = PrismaInferenceFeedback;

export type InferenceOutcome = {
  artifact_id: string;
  transform_hash: string;
  op_version: number;
  threshold_used: number;
  abstention_band: number;
  abstained: boolean;
  abstained_reason: string | null;
  latency_ms: number | null;
  inferred_at: string;
  probabilities: Record<string, number>[];
  label: TrainingDeformationLabel | TrainingSeismicLabel | null;
  score: number | null;
  interferogramId: string | null;
  seismicEventId: string | null;
  volcanoId: string | null;
};

export type InferenceLatest =
  | {
      kind: "deformation";
      inference: InferenceDeformation;
      feedback: InferenceFeedback | null;
    }
  | {
      kind: "seismic";
      inference: InferenceSeismic;
      feedback: InferenceFeedback | null;
    };

export type InferenceFeedbackDraft = {
  agreed: boolean | null;
  correctedDeformation: TrainingDeformationLabel | null;
  correctedSeismic: TrainingSeismicLabel | null;
  notes: string | null;
};

export type InferenceModalView = {
  label: TrainingDeformationLabel | TrainingSeismicLabel | null;
  score: number | InferenceDeformation["score"] | null;
  abstained: boolean;
  abstainedReason: string | null;
  artifactId: string | null;
  hasResult: boolean;
  submittedAgreed: boolean | null;
  submittedCorrectedDeformation: TrainingDeformationLabel | null;
  submittedCorrectedSeismic: TrainingSeismicLabel | null;
  submittedNotes: string | null;
  hasSubmitted: boolean;
};
