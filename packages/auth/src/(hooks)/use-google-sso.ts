"use client";

import { useState } from "react";
import { supabaseClient } from "../client/browser";
import { authRoutes } from "../routes";

export function useGoogleSso() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function handleGoogleSignIn() {
    setIsLoading(true);
    setError(null);
    const supabase = supabaseClient();
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}${authRoutes.auth.callback}`,
      },
    });
    if (error) {
      setError("Google sign in failed. Please try again.");
      setIsLoading(false);
    }
  }
  return { handleGoogleSignIn, isLoading, error };
}
