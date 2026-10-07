"use client";

import { useState } from "react";
import { supabaseClient } from "../client/browser";
import { authRoutes } from "../routes";

export function useOutlookSso() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function handleOutlookSignIn() {
    setIsLoading(true);
    setError(null);
    const supabase = supabaseClient();
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "azure",
      options: {
        redirectTo: `${window.location.origin}${authRoutes.auth.callback}`,
      },
    });
    if (error) {
      setError("Outlook sign in failed. Please try again.");
      setIsLoading(false);
    }
  }
  return { handleOutlookSignIn, isLoading, error };
}
