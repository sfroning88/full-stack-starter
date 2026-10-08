"use client";

import { useState, useEffect } from "react";

export function useMediaQuery(query: string, defaultMatch = false): boolean {
  const [matches, setMatches] = useState(defaultMatch);
  useEffect(() => {
    const media = window.matchMedia(query);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    media.addEventListener("change", handler);
    const id = requestAnimationFrame(() => setMatches(media.matches));
    return () => {
      cancelAnimationFrame(id);
      media.removeEventListener("change", handler);
    };
  }, [query]);
  return matches;
}
