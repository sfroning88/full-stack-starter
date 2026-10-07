import {
  VolcanoZone,
  VolcanoActivitySource,
  VolcanoAlertLevel,
} from "@fiery/db/enums";
import type {
  Prisma,
  Volcano as PrismaVolcano,
  VolcanoActivity as PrismaVolcanoActivity,
} from "@fiery/db";
import {
  InferenceDeformation,
  InferenceSeismic,
  InferenceFeedback,
} from "./inference-types";
import { ModelArtifact } from "./model-types";
import { TrainingInterferogram, TrainingSeismicEvent } from "./training-types";

export { VolcanoZone, VolcanoActivitySource, VolcanoAlertLevel };

export type Volcano = PrismaVolcano;
export type VolcanoActivity = PrismaVolcanoActivity;

type VolcanoSignalBundle<TSample, TInference> = {
  sample: TSample | null;
  inference: TInference | null;
  feedback: InferenceFeedback | null;
  artifact: Pick<ModelArtifact, "id" | "tier" | "role" | "promoted"> | null;
};

export type VolcanoDashboard = Volcano & {
  currentActivity: VolcanoActivity | null;
  deformation: VolcanoSignalBundle<TrainingInterferogram, InferenceDeformation>;
  seismic: {
    sample: TrainingSeismicEvent | null;
    cloud: VolcanoSignalBundle<never, InferenceSeismic>;
    edge: VolcanoSignalBundle<never, InferenceSeismic>;
  };
  _count: {
    activities: number;
    interferograms: number;
    seismicEvents: number;
  };
};

export type VolcanoDashboardRow = Prisma.VolcanoGetPayload<{
  include: typeof volcanoDashboardInclude;
}>;

export const volcanoDashboardInclude = {
  activities: {
    where: { isConfirmed: true },
    orderBy: { startedAt: "desc" },
    take: 1,
  },
  interferograms: {
    where: { storagePath: { not: "" } },
    orderBy: { createdAt: "desc" },
    take: 4,
    include: {
      inferences: {
        where: {
          artifact: { tier: "cloud", role: "screener", promoted: true },
        },
        orderBy: { inferredAt: "desc" },
        take: 1,
        include: {
          feedback: { orderBy: { createdAt: "desc" }, take: 1 },
          artifact: {
            select: { id: true, tier: true, role: true, promoted: true },
          },
        },
      },
    },
  },
  seismicEvents: {
    where: {
      OR: [{ waveformPath: { not: "" } }, { spectrogramPath: { not: null } }],
    },
    orderBy: { recordedAt: "desc" },
    take: 4,
    include: {
      inferences: {
        where: {
          OR: [
            {
              artifact: { tier: "cloud", role: "teacher", promoted: true },
            },
            {
              artifact: { tier: "edge", role: "student", promoted: true },
            },
          ],
        },
        orderBy: { inferredAt: "desc" },
        include: {
          artifact: {
            select: { id: true, tier: true, role: true, promoted: true },
          },
          feedback: { orderBy: { createdAt: "desc" }, take: 1 },
        },
      },
    },
  },
  _count: {
    select: { activities: true, interferograms: true, seismicEvents: true },
  },
} satisfies Prisma.VolcanoInclude;
