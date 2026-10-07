"use client";

import { type SubmitEvent, useState } from "react";
import { signInAction, signupAction } from "../(actions)/auth-action";
import { authRoutes } from "../routes";

export function useSignup(initialError?: string | null) {
  const [error, setError] = useState(initialError ?? null);
  const [isLoading, setIsLoading] = useState(false);
  async function handleSubmit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    const fd = new FormData(e.currentTarget);
    const email = String(fd.get("email") ?? "");
    const name = String(fd.get("name") ?? "");
    const password = String(fd.get("password") ?? "");
    const confirmPassword = String(fd.get("confirmPassword") ?? "");
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      setIsLoading(false);
      return;
    }
    const signup = await signupAction({ email, password, name });
    if (!signup.success) {
      setError(signup.error ?? "Failed to create account");
      setIsLoading(false);
      return;
    }
    const signIn = await signInAction({ email, password });
    if (signIn && !signIn.ok) {
      setError(signIn.error ?? "Account created, but sign in failed");
      setIsLoading(false);
      return;
    }
    window.location.href = authRoutes.root;
  }
  return { error, isLoading, handleSubmit };
}
