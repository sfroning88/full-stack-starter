import "server-only";

import { db, ModelTier } from "@fiery/db";
import {
  type ModelDashboard,
  modelDashboardInclude,
  type ApiKeyRequest,
  type ApiJobsResponse,
  type ApiIngestRequest,
  type ApiRefineRequest,
  type ApiRefineResponse,
  type ApiTrainRequest,
  type ApiTrainResponse,
  type ApiPromoteResponse,
  type ApiRefreshResponse,
} from "@fiery/types";
import { ApiAiService, ApiBackendService } from "@fiery/services";
import { toModelDashboard } from "@fiery/utils";

export class AdminService {
  private aiService: ApiAiService;
  private backendService: ApiBackendService;
  constructor() {
    this.aiService = ApiAiService.fromEnvironment();
    this.backendService = ApiBackendService.fromEnvironment();
  }

  async ingest(args: ApiIngestRequest): Promise<ApiJobsResponse> {
    return await this.aiService.ingest(args);
  }

  async refine(args: ApiRefineRequest): Promise<ApiRefineResponse> {
    return await this.aiService.refine(args);
  }

  async train(args: ApiTrainRequest): Promise<ApiTrainResponse> {
    return await this.aiService.train(args);
  }

  async batch(args: ApiKeyRequest): Promise<ApiJobsResponse> {
    return await this.backendService.batch(args);
  }

  async promote(): Promise<ApiPromoteResponse> {
    return await this.backendService.promote();
  }

  async refresh(args: ApiKeyRequest): Promise<ApiRefreshResponse> {
    return await this.backendService.refresh(args);
  }

  async fetchModels(): Promise<ModelDashboard[]> {
    const rows = await db.modelArtifact.findMany({
      include: modelDashboardInclude,
      orderBy: { createdAt: "desc" },
    });
    return rows.map(toModelDashboard);
  }

  async fetchWinners(): Promise<ModelDashboard[]> {
    const [cloud, edge] = await Promise.all([
      db.modelArtifact.findFirst({
        where: {
          tier: ModelTier.cloud,
          promoted: true,
          promotedAt: { not: null },
        },
        orderBy: { promotedAt: "desc" },
        include: modelDashboardInclude,
      }),
      db.modelArtifact.findFirst({
        where: {
          tier: ModelTier.edge,
          promoted: true,
          promotedAt: { not: null },
        },
        orderBy: { promotedAt: "desc" },
        include: modelDashboardInclude,
      }),
    ]);
    return [cloud, edge]
      .filter((row): row is NonNullable<typeof row> => row != null)
      .map(toModelDashboard);
  }
}
