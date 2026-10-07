import { use } from "react";
import type { ModelDashboard } from "@fiery/types";
import { AdminPanel } from "./AdminPanel";

type AdminAsyncProps = {
  initialWinnersPromise: Promise<ModelDashboard[]>;
  initialModelsPromise: Promise<ModelDashboard[]>;
};

export function AdminAsync({
  initialWinnersPromise,
  initialModelsPromise,
}: AdminAsyncProps) {
  const [initialWinners, initialModels] = use(
    Promise.all([initialWinnersPromise, initialModelsPromise]),
  );
  return (
    <AdminPanel initialWinners={initialWinners} initialModels={initialModels} />
  );
}
