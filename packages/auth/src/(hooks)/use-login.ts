"use client";

import { type SubmitEvent, useState } from "react";
import { signInAction } from "../(actions)/auth-action";
import { authRoutes } from "../routes";

export function useLogin(initialError?: string | null) {
  const [error, setError] = useState(initialError ?? null);
  const [isLoading, setIsLoading] = useState(false);
  async function handleSubmit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    const form = e.currentTarget;
    const fd = new FormData(form);
    const email = String(fd.get("email") ?? "");
    const password = String(fd.get("password") ?? "");
    if (password.length < 5) {
      setError("Invalid email or password");
      setIsLoading(false);
      return;
    }
    try {
      const res = await signInAction({ email, password });
      if (res && !res.ok) {
        setError(res.error ?? "Sign in failed");
        setIsLoading(false);
        return;
      }
      if (res?.ok) {
        window.location.href = authRoutes.root;
      }
    } catch {
      setError("Sign in failed");
      setIsLoading(false);
    }
  }
  return { error, isLoading, handleSubmit };
}
