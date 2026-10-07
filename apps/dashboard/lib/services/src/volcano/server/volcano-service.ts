import "server-only";

import { db, TrainingDeformationLabel, TrainingSeismicLabel } from "@fiery/db";
import {
  type VolcanoDashboard,
  volcanoDashboardInclude,
  type ApiInferenceRequest,
  type ApiInferenceResponse,
  type ApiPreviewRequest,
  type ApiPreviewResponse,
} from "@fiery/types";
import { toVolcanoDashboard } from "@fiery/utils";
import { ApiBackendService } from "@fiery/services";

export class VolcanoService {
  private backendService: ApiBackendService;
  constructor() {
    this.backendService = ApiBackendService.fromEnvironment();
  }

  async preview(args: ApiPreviewRequest): Promise<ApiPreviewResponse> {
    if (
      (!args.interferogramId && !args.seismicEventId) ||
      (args.interferogramId && args.seismicEventId)
    )
      throw new Error("Malformed preview");
    const buffer = await this.backendService.preview(args);
    return {
      contentType: "image/png",
      base64: Buffer.from(buffer).toString("base64"),
    };
  }

  async inference(args: ApiInferenceRequest): Promise<ApiInferenceResponse> {
    if (
      (!args.interferogramId && !args.seismicEventId) ||
      (args.interferogramId && args.seismicEventId)
    )
      throw new Error("Malformed inference");
    return await this.backendService.inference(args);
  }

  async feedback(
    agreed: boolean,
    correctedDeformation: TrainingDeformationLabel | null,
    correctedSeismic: TrainingSeismicLabel | null,
    note: string | null,
    interferogramId: string | null,
    seismicEventId: string | null,
    userId: string | null,
    artifactId: string,
  ): Promise<void> {
    let data = null;
    if (
      (!correctedDeformation && !correctedSeismic) ||
      (correctedDeformation && correctedSeismic) ||
      (!interferogramId && !seismicEventId) ||
      (interferogramId && seismicEventId)
    ) {
      throw new Error("Malformed feedback");
    }
    if (correctedDeformation && interferogramId) {
      data = {
        agreed: agreed,
        correctedDeformation: correctedDeformation,
        note: note,
        interferogramId: interferogramId,
        userId: userId,
        artifactId: artifactId,
      };
    } else if (correctedSeismic && seismicEventId) {
      data = {
        agreed: agreed,
        correctedSeismic: correctedSeismic,
        note: note,
        seismicEventId: seismicEventId,
        userId: userId,
        artifactId: artifactId,
      };
    }
    if (!data) {
      throw new Error("Missing deformation/interferogram or seismic/event");
    }
    await db.inferenceFeedback.create({
      data: data,
    });
  }

  async fetchVolcanoes(): Promise<VolcanoDashboard[]> {
    const rows = await db.volcano.findMany({
      include: volcanoDashboardInclude,
    });
    return rows.map(toVolcanoDashboard);
  }
}
