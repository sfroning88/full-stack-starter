"use server";

import { z } from "zod";
import { platformAdminAction } from "@fiery/auth/server";
import { AdminService } from "@lib/services";
import {
  ModelTier,
  ModelRole,
  ModelDashboard,
  TrainingSampleSource,
  TrainingStage,
  type ApiJobsResponse,
  type ApiRefineResponse,
  type ApiTrainResponse,
  type ApiPromoteResponse,
  type ApiRefreshResponse,
} from "@fiery/types";

const adminService = new AdminService();

const ingestSchema = z.object({
  source: z.nativeEnum(TrainingSampleSource),
  maxSamples: z.number().int().nullable(),
});

export const ingestAction = platformAdminAction(
  ingestSchema,
  async (ctx): Promise<ApiJobsResponse> => {
    return await adminService.ingest({
      source: ctx.source,
      maxSamples: ctx.maxSamples,
    });
  },
);

const refineSchema = z.object({
  contractId: z.string().uuid().min(1),
  maxSamples: z.number().int().nullable(),
});

export const refineAction = platformAdminAction(
  refineSchema,
  async (ctx): Promise<ApiRefineResponse> => {
    return await adminService.refine({
      contractId: ctx.contractId,
      maxSamples: ctx.maxSamples,
    });
  },
);

const trainSchema = z.object({
  contractId: z.string().uuid().min(1),
  versionId: z.string().uuid().min(1),
  stage: z.nativeEnum(TrainingStage),
  parentId: z.string().uuid().nullable(),
});

export const trainAction = platformAdminAction(
  trainSchema,
  async (ctx): Promise<ApiTrainResponse> => {
    return await adminService.train({
      contractId: ctx.contractId,
      versionId: ctx.versionId,
      stage: ctx.stage,
      parentId: ctx.parentId,
    });
  },
);

const batchSchema = z.object({
  tier: z.nativeEnum(ModelTier),
  role: z.nativeEnum(ModelRole),
});

export const batchAction = platformAdminAction(
  batchSchema,
  async (ctx): Promise<ApiJobsResponse> => {
    return await adminService.batch({
      tier: ctx.tier,
      role: ctx.role,
    });
  },
);

const promoteSchema = z.void();

export const promoteAction = platformAdminAction(
  promoteSchema,
  async (): Promise<ApiPromoteResponse> => {
    return await adminService.promote();
  },
);

const refreshSchema = z.object({
  tier: z.nativeEnum(ModelTier),
  role: z.nativeEnum(ModelRole),
});

export const refreshAction = platformAdminAction(
  refreshSchema,
  async (ctx): Promise<ApiRefreshResponse> => {
    return await adminService.refresh({
      tier: ctx.tier,
      role: ctx.role,
    });
  },
);

const fetchModelsSchema = z.void();

export const fetchModelsAction = platformAdminAction(
  fetchModelsSchema,
  async (): Promise<ModelDashboard[]> => {
    return await adminService.fetchModels();
  },
);

export const fetchWinnersAction = platformAdminAction(
  fetchModelsSchema,
  async (): Promise<ModelDashboard[]> => {
    return await adminService.fetchWinners();
  },
);
