import { ApiServiceConfig } from "@fiery/types";

export class ApiService {
  protected config: ApiServiceConfig;
  constructor(config: ApiServiceConfig) {
    this.config = {
      timeout: 30 * 1000,
      ...config,
    };
  }

  protected async makeRequest<T = unknown>(
    endpoint: string,
    options: RequestInit,
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);
    try {
      const response = await fetch(endpoint, {
        ...options,
        headers: {
          "auth-token": this.config.authToken,
          ...options.headers,
        },
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (!response.ok) {
        const errorData = (await response.json().catch(() => ({}))) as Record<
          string,
          unknown
        >;
        throw new ApiServiceError(
          `Request failed with status ${response.status}`,
          response.status,
          errorData,
        );
      }
      return (await response.json()) as T;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  protected async makeBinaryRequest(
    endpoint: string,
    options: RequestInit,
  ): Promise<ArrayBuffer> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);
    try {
      const response = await fetch(endpoint, {
        ...options,
        headers: {
          "auth-token": this.config.authToken,
          ...options.headers,
        },
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (!response.ok) {
        const errorData = (await response.json().catch(() => ({}))) as Record<
          string,
          unknown
        >;
        throw new ApiServiceError(
          `Request failed with status ${response.status}`,
          response.status,
          errorData,
        );
      }
      return await response.arrayBuffer();
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  protected handleError(error: unknown, message: string): ApiServiceError {
    if (error instanceof ApiServiceError) {
      return error;
    }
    if (error instanceof Error) {
      if (error.name === "AbortError") {
        return new ApiServiceError("Request timeout", 408, {
          originalError: error.message,
        });
      }
      return new ApiServiceError(message, 500, {
        originalError: error.message,
      });
    }
    return new ApiServiceError(message, 500, {
      originalError: String(error),
    });
  }
}

export class ApiServiceError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "ApiServiceError";
  }
}
