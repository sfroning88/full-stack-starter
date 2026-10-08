import { env } from "@my-project/config";
import {
  API_ROUTES,
  type ApiRequest,
  type ApiJobsResponse,
} from "@my-project/types";
import { ApiService } from "../api-service";

export class ApiBackendService extends ApiService {
  static fromEnvironment(): ApiBackendService {
    const baseUrl = env.BACKEND_API_URL ?? "";
    const authToken = env.AUTH_TOKEN ?? "";
    if (!baseUrl || !authToken) {
      throw new Error("Missing environment config");
    }
    return new ApiBackendService({ baseUrl, authToken, timeout: 300000 });
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async message(_request: ApiRequest): Promise<ApiJobsResponse> {
    const endpoint = `${this.config.baseUrl}${API_ROUTES.message()}`;
    return this.makeRequest<ApiJobsResponse>(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  }
}
