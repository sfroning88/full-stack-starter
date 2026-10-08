import { createRoute } from "./route-types";

export type ApiServiceConfig = {
  baseUrl: string;
  authToken: string;
  timeout?: number;
};

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export type ApiRequest = {
  // empty
};

export type ApiJobsResponse = {
  jobIds: string[];
};

export const API_ROUTES = {
  // apps/backend: print message
  message: createRoute("/api/message"),
};
