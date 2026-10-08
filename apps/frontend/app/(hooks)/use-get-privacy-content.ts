"use client";

import { useState, useEffect, useRef } from "react";
import { getPrivacyContentAction } from "@/app/(actions)/privacy-action";

export function useGetPrivacyContent(isOpen: boolean) {
  const [content, setContent] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const isFetchingRef = useRef(false);
  useEffect(() => {
    if (isOpen && !content && !isFetchingRef.current) {
      isFetchingRef.current = true;
      queueMicrotask(() => {
        setIsLoading(true);
        getPrivacyContentAction({})
          .then((data: string) => setContent(data))
          .finally(() => {
            setIsLoading(false);
            isFetchingRef.current = false;
          });
      });
    }
  }, [isOpen, content]);
  return { content, isLoading };
}
