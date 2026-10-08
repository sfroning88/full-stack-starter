import "server-only";

import { db } from "@my-project/db";
import {
  type MyClass,
  type ApiRequest,
  type ApiJobsResponse,
} from "@my-project/types";
import { ApiBackendService } from "@my-project/services";

export class AdminService {
  private backendService: ApiBackendService;
  constructor() {
    this.backendService = ApiBackendService.fromEnvironment();
  }

  async message(args: ApiRequest): Promise<ApiJobsResponse> {
    return await this.backendService.message(args);
  }

  async fetchMessages(): Promise<MyClass[]> {
    return await db.myClass.findMany();
  }
}
