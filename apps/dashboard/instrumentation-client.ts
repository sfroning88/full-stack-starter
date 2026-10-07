import { env } from "@fiery/config";
import posthog from "posthog-js";

function posthogUiHostFromApiHost(apiHostUrl: string): string {
  try {
    const { hostname } = new URL(apiHostUrl);
    const region = hostname.startsWith("eu.") ? "eu" : "us";
    return `https://${region}.posthog.com`;
  } catch {
    return "https://us.posthog.com";
  }
}

posthog.init(env.NEXT_PUBLIC_POSTHOG_KEY, {
  api_host: "/ingest",
  ui_host: posthogUiHostFromApiHost(env.NEXT_PUBLIC_POSTHOG_HOST),
  // Include the defaults option as required by PostHog
  defaults: "2026-01-30",
  // Enables capturing unhandled exceptions via Error Tracking
  capture_exceptions: true,
  // Turn on debug in development mode
  debug: process.env.NODE_ENV === "development",
});

//IMPORTANT: Never combine this approach with other client-side PostHog initialization approaches, especially components like a PostHogProvider. instrumentation-client.ts is the correct solution for initializating client-side PostHog in Next.js 15.3+ apps.
