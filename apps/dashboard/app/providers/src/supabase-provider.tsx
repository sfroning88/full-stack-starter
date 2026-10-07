"use client";

import { createContext, useContext, useMemo } from "react";
import type { SupabaseClient } from "@supabase/supabase-js";
import { supabaseClient } from "@fiery/auth";

const SupabaseContext = createContext<SupabaseClient | null>(null);

export function SupabaseProvider({ children }: { children: React.ReactNode }) {
  const client = useMemo(() => supabaseClient(), []);
  return (
    <SupabaseContext.Provider value={client}>
      {children}
    </SupabaseContext.Provider>
  );
}

export function useSupabase() {
  const ctx = useContext(SupabaseContext);
  if (!ctx) {
    throw new Error("useSupabase must be used within SupabaseProvider");
  }
  return ctx;
}
