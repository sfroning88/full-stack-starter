"use client";

import { useState } from "react";
import { getOrCreateUserId } from "@/lib/utils/src/cookie-utils";

export function useUserId(): string {
  const [userId] = useState<string>(() => getOrCreateUserId() || "");
  return userId;
}
