"use client";

import { useEffect, useState } from "react";
import { Button } from "@fiery/ui";

type LoginSubmitProps = {
  isLoading: boolean;
};

export function LoginSubmit({ isLoading }: LoginSubmitProps) {
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => setHydrated(true), []);
  return (
    <Button
      type={hydrated ? "submit" : "button"}
      disabled={!hydrated || isLoading}
      data-hydrated={hydrated ? "true" : "false"}
      data-testid="login-submit"
      className="w-full"
    >
      {isLoading ? "Signing in..." : "Sign in"}
    </Button>
  );
}
