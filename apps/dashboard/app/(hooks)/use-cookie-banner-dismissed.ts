"use client";

import { useSyncExternalStore } from "react";
import {
  COOKIE_BANNER_DISMISSED_KEY,
  COOKIE_BANNER_SYNC_EVENT,
} from "@/lib/constants";

function getSnapshot(): boolean {
  if (typeof window === "undefined") return true;
  return localStorage.getItem(COOKIE_BANNER_DISMISSED_KEY) === "true";
}

function getServerSnapshot(): boolean {
  return true;
}

function subscribe(onStoreChange: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  const handler = () => onStoreChange();
  window.addEventListener(COOKIE_BANNER_SYNC_EVENT, handler);
  window.addEventListener("storage", handler);
  return () => {
    window.removeEventListener(COOKIE_BANNER_SYNC_EVENT, handler);
    window.removeEventListener("storage", handler);
  };
}

export function useCookieBannerDismissed(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
