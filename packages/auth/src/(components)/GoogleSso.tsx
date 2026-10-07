"use client";

import { Google } from "iconoir-react";
import { Button } from "@fiery/ui";
import { useGoogleSso } from "../(hooks)/use-google-sso";

export function GoogleSso() {
  const { handleGoogleSignIn, isLoading, error } = useGoogleSso();
  return (
    <div className="flex flex-col gap-2">
      <Button
        onClick={handleGoogleSignIn}
        disabled={isLoading}
        className="w-full"
      >
        <Google className="h-4 w-4 shrink-0" />
        {isLoading ? "Redirecting..." : "Sign in with Google"}
      </Button>
      {error ? (
        <p className="text-xs font-semibold text-white">{error}</p>
      ) : null}
    </div>
  );
}
