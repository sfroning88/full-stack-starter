import type { NextConfig } from "next";
import path from "node:path";

/** PostHog reverse proxy targets — see https://posthog.com/docs/advanced/proxy/nextjs */
function getPostHogRewriteDestinations() {
  const raw =
    process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com";
  try {
    const { hostname } = new URL(raw);
    const region = hostname.startsWith("eu.") ? "eu" : "us";
    return {
      api: `https://${region}.i.posthog.com`,
      assets: `https://${region}-assets.i.posthog.com`,
    };
  } catch {
    return {
      api: "https://us.i.posthog.com",
      assets: "https://us-assets.i.posthog.com",
    };
  }
}

const nextConfig: NextConfig = {
  // Monorepo: trace files from repo root (see output caveats in Next.js docs).
  outputFileTracingRoot: path.join(process.cwd(), "../.."),
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**", pathname: "**" },
      { protocol: "http", hostname: "**", pathname: "**" },
    ],
  },
  // Required so PostHog paths with trailing slashes are not redirected away from the proxy.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    const { api, assets } = getPostHogRewriteDestinations();
    return [
      {
        source: "/ingest/static/:path*",
        destination: `${assets}/static/:path*`,
      },
      {
        source: "/ingest/array/:path*",
        destination: `${assets}/array/:path*`,
      },
      {
        source: "/ingest/:path*",
        destination: `${api}/:path*`,
      },
    ];
  },
};

export default nextConfig;
