"use client";

import type { ReactNode } from "react";

type AdminMutationMessageProps = {
  isError: boolean;
  isSuccess: boolean;
  error: unknown;
  fallbackError: string;
  children?: ReactNode;
};

export function AdminMutationMessage({
  isError,
  isSuccess,
  error,
  fallbackError,
  children,
}: AdminMutationMessageProps) {
  if (isError) {
    return (
      <p className="text-red-400 text-sm">
        {error instanceof Error ? error.message : fallbackError}
      </p>
    );
  }

  if (isSuccess && children != null) {
    return <p className="text-green-400 text-sm">{children}</p>;
  }

  return null;
}
