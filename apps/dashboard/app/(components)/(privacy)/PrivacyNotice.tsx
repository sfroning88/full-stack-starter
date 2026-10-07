"use client";

import { useCallback, useLayoutEffect, useState } from "react";
import { createPortal } from "react-dom";
import posthog from "posthog-js";
import ReactMarkdown from "react-markdown";
import { useCookieBannerDismissed } from "@/app/(hooks)/use-cookie-banner-dismissed";
import { useMediaQuery } from "@/app/(hooks)/use-media-query";
import { MOBILE_BREAKPOINT } from "@/lib/constants";
import { POSTHOG_EVENTS } from "@fiery/types";
import { useModalFocus } from "@/app/(hooks)/use-modal-focus";
import { useGetPrivacyContent } from "@/app/(hooks)/use-get-privacy-content";

export function PrivacyNotice() {
  const cookieBannerDismissed = useCookieBannerDismissed();
  const isMobile = !useMediaQuery(`(min-width: ${MOBILE_BREAKPOINT}px)`, true);
  const [layoutReady, setLayoutReady] = useState(false);
  useLayoutEffect(() => setLayoutReady(true), []);
  const stackAboveBanner = layoutReady && !cookieBannerDismissed;
  const [isOpen, setIsOpen] = useState(false);
  const { content, isLoading } = useGetPrivacyContent(isOpen);
  const handleOpen = () => {
    setIsOpen(true);
    posthog.capture(POSTHOG_EVENTS.privacy_policy_opened);
  };
  const handleClose = useCallback(() => {
    setIsOpen(false);
    posthog.capture(POSTHOG_EVENTS.privacy_policy_closed);
  }, []);
  const dialogRef = useModalFocus(isOpen, handleClose);
  const modalContent = isOpen ? (
    <>
      <div
        className="fixed inset-0 bg-black/50 z-100"
        onClick={handleClose}
        aria-hidden
      />
      <div
        ref={dialogRef}
        tabIndex={-1}
        role="dialog"
        aria-modal
        aria-labelledby="privacy-title"
        className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-card border border-border shadow-lg z-110 flex flex-col gap-4 overflow-hidden transition-all duration-300 max-w-2xl max-h-[80vh] w-[90vw] rounded-sm outline-none"
        style={{ padding: isMobile ? "0.75rem" : "1.5rem" }}
      >
        <div className="flex items-center justify-between shrink-0">
          <h2
            id="privacy-title"
            className={`font-semibold truncate ${isMobile ? "text-base" : "text-xl"}`}
          >
            Privacy Policy
          </h2>
          <button
            type="button"
            onClick={handleClose}
            className={`text-muted-foreground hover:text-card-foreground leading-none ${isMobile ? "text-xl" : "text-2xl"}`}
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div
          className={`overflow-auto flex-1 prose max-w-none min-w-0 ${
            isMobile
              ? "text-xs prose-sm prose-p:text-xs prose-li:text-xs prose-headings:text-sm"
              : "text-sm prose-sm"
          }`}
        >
          {isLoading ? (
            <span className={isMobile ? "text-xs" : "text-sm"}>Loading...</span>
          ) : (
            <ReactMarkdown>{content}</ReactMarkdown>
          )}
        </div>
      </div>
    </>
  ) : null;
  return (
    <>
      <button
        type="button"
        onClick={handleOpen}
        className={`fixed right-4 bg-card border border-border shadow-sm hover:bg-secondary z-50 font-medium text-card-foreground font-data rounded-sm ${
          !stackAboveBanner ? "bottom-4" : isMobile ? "bottom-52" : "bottom-46"
        } ${isMobile ? "px-3 py-2 text-xs rounded-sm" : "px-4 py-2 text-sm rounded-sm"}`}
      >
        Privacy
      </button>
      {typeof window !== "undefined" && modalContent
        ? createPortal(modalContent, document.body)
        : modalContent}
    </>
  );
}
