"use client";

import { createPortal } from "react-dom";
import posthog from "posthog-js";
import { toast } from "sonner";
import { useCookieBannerDismissed } from "@/app/(hooks)/use-cookie-banner-dismissed";
import { useMediaQuery } from "@/app/(hooks)/use-media-query";
import {
  COOKIE_BANNER_DISMISSED_KEY,
  COOKIE_BANNER_MESSAGE,
  COOKIE_BANNER_SYNC_EVENT,
  MOBILE_BREAKPOINT,
} from "@/lib/constants";
import { POSTHOG_EVENTS } from "@fiery/types";

export function CookieBanner() {
  const isMobile = !useMediaQuery(`(min-width: ${MOBILE_BREAKPOINT}px)`, true);
  const dismissed = useCookieBannerDismissed();

  const handleDismiss = () => {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem(COOKIE_BANNER_DISMISSED_KEY, "true");
      window.dispatchEvent(new Event(COOKIE_BANNER_SYNC_EVENT));
    }
    posthog.capture(POSTHOG_EVENTS.cookie_banner_dismissed);
    toast.success("Cookie notice dismissed.");
  };

  if (dismissed) {
    return null;
  }

  const banner = (
    <div
      className={`fixed bottom-4 right-4 z-40 flex flex-col gap-2 bg-card border border-border shadow-sm font-display uppercase tracking-wide text-card-foreground rounded-sm ${
        isMobile
          ? "max-w-[calc(100vw-2rem)] p-3 text-[10px] leading-snug"
          : "max-w-sm p-4 text-xs leading-snug"
      }`}
      role="region"
      aria-labelledby="cookie-banner-title"
      aria-describedby="cookie-banner-desc"
    >
      <div className="flex items-start justify-between gap-3">
        <h2
          id="cookie-banner-title"
          className={`font-semibold shrink-0 ${isMobile ? "text-[11px]" : "text-sm"}`}
        >
          Cookie notice
        </h2>
        <button
          type="button"
          onClick={handleDismiss}
          className="-mr-1 -mt-1 text-muted-foreground hover:text-card-foreground leading-none shrink-0 text-lg font-normal tracking-normal px-1 min-h-[44px] min-w-[44px] flex items-start justify-end sm:min-h-0 sm:min-w-0"
          aria-label="Dismiss cookie notice"
        >
          ×
        </button>
      </div>
      <p id="cookie-banner-desc" className="text-muted-foreground font-normal">
        {COOKIE_BANNER_MESSAGE}
      </p>
    </div>
  );

  return typeof window !== "undefined"
    ? createPortal(banner, document.body)
    : null;
}
