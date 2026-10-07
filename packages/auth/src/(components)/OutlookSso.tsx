"use client";

import { Windows } from "iconoir-react";
import { Button } from "@fiery/ui";
import { useOutlookSso } from "../(hooks)/use-outlook-sso";

export function OutlookSso() {
  const { handleOutlookSignIn, isLoading, error } = useOutlookSso();
  return (
    <div className="flex flex-col gap-2">
      <Button
        onClick={handleOutlookSignIn}
        disabled={isLoading}
        className="w-full"
      >
        <Windows className="h-4 w-4 shrink-0" />
        {isLoading ? "Redirecting..." : "Sign in with Outlook"}
      </Button>
      {error ? (
        <p className="text-xs font-semibold text-white">{error}</p>
      ) : null}
    </div>
  );
}
