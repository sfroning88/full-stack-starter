"use server";

import { z } from "zod";
import { createPublicAction, selfUserAction } from "@fiery/auth/server";
import { VolcanoService } from "@lib/services";
import {
  ModelTier,
  ModelRole,
  TrainingDeformationLabel,
  TrainingSeismicLabel,
  VolcanoDashboard,
  type ApiInferenceResponse,
  type ApiPreviewResponse,
} from "@fiery/types";

const volcanoService = new VolcanoService();

const previewSchema = z.object({
  interferogramId: z.string().uuid().nullable(),
  seismicEventId: z.string().uuid().nullable(),
});

export const previewAction = selfUserAction(
  previewSchema,
  async (ctx): Promise<ApiPreviewResponse | null> => {
    if (
      (!ctx.interferogramId && !ctx.seismicEventId) ||
      (ctx.interferogramId && ctx.seismicEventId)
    )
      return null;
    return await volcanoService.preview({
      interferogramId: ctx.interferogramId,
      seismicEventId: ctx.seismicEventId,
    });
  },
);

const inferenceSchema = z.object({
  tier: z.nativeEnum(ModelTier),
  role: z.nativeEnum(ModelRole),
  interferogramId: z.string().uuid().nullable(),
  seismicEventId: z.string().uuid().nullable(),
  volcanoId: z.string().uuid().nullable(),
});

export const inferenceAction = selfUserAction(
  inferenceSchema,
  async (ctx): Promise<ApiInferenceResponse | null> => {
    if (
      (!ctx.interferogramId && !ctx.seismicEventId) ||
      (ctx.interferogramId && ctx.seismicEventId)
    )
      return null;
    return await volcanoService.inference({
      tier: ctx.tier,
      role: ctx.role,
      interferogramId: ctx.interferogramId,
      seismicEventId: ctx.seismicEventId,
      volcanoId: ctx.volcanoId,
    });
  },
);

const feedbackSchema = z.object({
  agreed: z.boolean(),
  correctedDeformation: z.nativeEnum(TrainingDeformationLabel).nullable(),
  correctedSeismic: z.nativeEnum(TrainingSeismicLabel).nullable(),
  note: z.string().nullable(),
  interferogramId: z.string().uuid().nullable(),
  seismicEventId: z.string().uuid().nullable(),
  artifactId: z.string().uuid().min(1),
});

export const feedbackAction = selfUserAction(
  feedbackSchema,
  async (ctx): Promise<void> => {
    if (
      (!ctx.correctedDeformation && !ctx.correctedSeismic) ||
      (ctx.correctedDeformation && ctx.correctedSeismic) ||
      (!ctx.interferogramId && !ctx.seismicEventId) ||
      (ctx.interferogramId && ctx.seismicEventId)
    )
      return;
    await volcanoService.feedback(
      ctx.agreed,
      ctx.correctedDeformation,
      ctx.correctedSeismic,
      ctx.note,
      ctx.interferogramId,
      ctx.seismicEventId,
      ctx.userId,
      ctx.artifactId,
    );
  },
);

const fetchVolcanoesSchema = z.void();

export const fetchVolcanoesAction = createPublicAction(
  fetchVolcanoesSchema,
  async (): Promise<VolcanoDashboard[]> => {
    return await volcanoService.fetchVolcanoes();
  },
);
