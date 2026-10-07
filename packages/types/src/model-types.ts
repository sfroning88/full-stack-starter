import { ModelTier, ModelRole, ModelMetricName } from "@fiery/db/enums";
import {
  Prisma,
  type ModelArtifact as PrismaModelArtifact,
  type ModelMetric as PrismaModelMetric,
  type ModelBudget as PrismaModelBudget,
} from "@fiery/db";
import { DatasetVersion } from "./dataset-types";
import {
  TrainingSignal,
  TrainingStage,
  TrainingStatus,
  TrainingContract,
} from "./training-types";

export { ModelTier, ModelRole, ModelMetricName };

export type ModelArtifact = PrismaModelArtifact;
export type ModelMetric = PrismaModelMetric;
export type ModelBudget = PrismaModelBudget;

export type ModelBudgetMetricName =
  "flash" | "peakRam" | "macs" | "latency" | "energy" | "autonomy";

export type ModelBudgetMetric = {
  name: ModelBudgetMetricName;
  value: number;
  budget: number | null;
};

export type EvaluatedModel = {
  artifact_id: string;
  tier: ModelTier;
  role: ModelRole;
  evaluated_at: string | null;
  promoted: boolean;
  promoted_at: string | null;
  denied_reason: string | null;
  ready: boolean;
};

export type ModelDashboard = ModelArtifact & {
  metrics: ModelMetric[];
  budget: ModelBudget | null;
  session: {
    id: string;
    signal: TrainingSignal;
    stage: TrainingStage;
    status: TrainingStatus;
    samples: number;
    startedAt: Date | null;
    finishedAt: Date | null;
    contract: Pick<TrainingContract, "id" | "signal" | "version">;
    version: Pick<DatasetVersion, "id" | "transformHash" | "sampleCount">;
  };
  parent: Pick<
    ModelArtifact,
    | "id"
    | "tier"
    | "role"
    | "stage"
    | "architecture"
    | "promoted"
    | "promotedAt"
  > | null;
  _count: {
    children: number;
    deformationInferences: number;
    seismicInferences: number;
    feedback: number;
  };
};

export type ModelDashboardRow = Prisma.ModelArtifactGetPayload<{
  include: typeof modelDashboardInclude;
}>;

export const modelDashboardInclude = {
  metrics: true,
  budget: true,
  session: {
    select: {
      id: true,
      signal: true,
      stage: true,
      status: true,
      samples: true,
      startedAt: true,
      finishedAt: true,
      contract: {
        select: {
          id: true,
          signal: true,
          version: true,
        },
      },
      version: {
        select: {
          id: true,
          transformHash: true,
          sampleCount: true,
        },
      },
    },
  },
  parent: {
    select: {
      id: true,
      tier: true,
      role: true,
      stage: true,
      architecture: true,
      promoted: true,
      promotedAt: true,
    },
  },
  _count: {
    select: {
      children: true,
      deformationInferences: true,
      seismicInferences: true,
      feedback: true,
    },
  },
} satisfies Prisma.ModelArtifactInclude;
