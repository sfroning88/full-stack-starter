"use client";

import { AdminModel } from "./AdminModel";
import { TEST_IDS } from "@lib/test-ids";
import { Button, SectionLabel } from "@fiery/ui";
import type { ModelDashboard } from "@fiery/types";

type AdminCatalogProps = {
  isMobile: boolean;
  winnersLoading: boolean;
  winnersError: boolean;
  winnersErrorDetail: unknown;
  winners: readonly ModelDashboard[];
  loadAll: boolean;
  onLoadAll: () => void;
  allModelsLoading: boolean;
  allModelsError: boolean;
  allModelsErrorDetail: unknown;
  remainingModels: ModelDashboard[];
};

export function AdminCatalog({
  isMobile,
  winnersLoading,
  winnersError,
  winnersErrorDetail,
  winners,
  loadAll,
  onLoadAll,
  allModelsLoading,
  allModelsError,
  allModelsErrorDetail,
  remainingModels,
}: AdminCatalogProps) {
  if (winnersLoading) {
    return <p className="text-white/50 text-sm">Loading current winners…</p>;
  }

  if (winnersError) {
    return (
      <p className="text-red-400 text-sm">
        {winnersErrorDetail instanceof Error
          ? winnersErrorDetail.message
          : "Could not load current winners."}
      </p>
    );
  }

  return (
    <div className="space-y-2">
      <SectionLabel>current winners</SectionLabel>
      {!winners.length ? (
        <p className="text-white/40 text-sm">No promoted models yet…</p>
      ) : (
        <ul className="border border-white/10 rounded-md overflow-hidden bg-surface-dark">
          {winners.map((model) => (
            <AdminModel
              key={model.id}
              model={model}
              isMobile={isMobile}
              showTrophy
            />
          ))}
        </ul>
      )}
      {!loadAll ? (
        <Button data-testid={TEST_IDS.loadAllModelsButton} onClick={onLoadAll}>
          Load All
        </Button>
      ) : allModelsLoading ? (
        <p className="text-white/50 text-sm">Loading all models…</p>
      ) : allModelsError ? (
        <p className="text-red-400 text-sm">
          {allModelsErrorDetail instanceof Error
            ? allModelsErrorDetail.message
            : "Could not load all models."}
        </p>
      ) : remainingModels.length > 0 ? (
        <div className="space-y-2">
          <SectionLabel>all models</SectionLabel>
          <ul className="border border-white/10 rounded-md overflow-hidden bg-surface-dark">
            {remainingModels.map((model) => (
              <AdminModel key={model.id} model={model} isMobile={isMobile} />
            ))}
          </ul>
        </div>
      ) : (
        <p className="text-white/40 text-sm">No other models to show.</p>
      )}
    </div>
  );
}
