import { createRoute } from "./route-types";
import { ModelTier, ModelRole, EvaluatedModel } from "./model-types";
import { InferenceOutcome } from "./inference-types";
import { TrainingSampleSource, TrainingStage } from "@fiery/db";

export type ApiServiceConfig = {
  baseUrl: string;
  authToken: string;
  timeout?: number;
};

export type ApiKeyRequest = {
  tier: ModelTier;
  role: ModelRole;
};

export type ApiJobsResponse = {
  jobIds: string[];
};

export type ApiIngestRequest = {
  source: TrainingSampleSource;
  maxSamples: number | null;
};

export type ApiRefineRequest = {
  contractId: string;
  maxSamples: number | null;
};

export type ApiRefineResponse = ApiJobsResponse & {
  versionId: string;
  transformHash: string;
  cached: boolean;
};

export type ApiTrainRequest = {
  contractId: string;
  versionId: string;
  stage: TrainingStage;
  parentId: string | null;
};

export type ApiTrainResponse = ApiJobsResponse & {
  sessionId: string;
  cached: boolean;
};

export type ApiInferenceRequest = {
  tier: ModelTier;
  role: ModelRole;
  interferogramId: string | null;
  seismicEventId: string | null;
  volcanoId: string | null;
};

export type ApiInferenceResponse = {
  result: InferenceOutcome;
  artifactId: string;
  transformHash: string;
};

export type ApiPreviewRequest = {
  interferogramId: string | null;
  seismicEventId: string | null;
};

export type ApiPreviewResponse = {
  contentType: string;
  base64: string;
};

export type ApiPromoteResponse = {
  evaluatedModels: EvaluatedModel[];
};

export type ApiRefreshResponse = {
  artifactId: string;
  tier: ModelTier;
  role: ModelRole;
  ready: boolean;
};

export const API_ROUTES = {
  // apps/ai: ingest from hephaestus, okada, or llaima source
  ingest: createRoute("/api/ingest"),

  // apps/ai: refine deformation or seismic samples
  refine: createRoute("/api/refine"),

  // apps/ai: enqueue pretrain, lora, distill, prune, or quantize job
  train: createRoute("/api/train"),

  // apps/backend: png preview for interferogram or seismic sample
  preview: createRoute("/api/preview"),

  // apps/backend: inference for given interferogram, seismic event, or volcano
  inference: createRoute("/api/inference/single"),

  // apps/backend: inference cache by key
  batch: createRoute("/api/inference/batch"),

  // apps/backend: force check for pending promotions
  promote: createRoute("/api/ml/promote"),

  // apps/backend: force model reload by key
  refresh: createRoute("/api/ml/refresh"),
};
