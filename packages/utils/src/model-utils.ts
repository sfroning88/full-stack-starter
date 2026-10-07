import {
  ModelDashboard,
  ModelDashboardRow,
  ModelMetric,
  ModelBudget,
  ModelBudgetMetricName,
  ModelBudgetMetric,
  ModelTier,
} from "@fiery/types";
import { dateLikeToMs, toNum } from "./number-utils";

export function toModelDashboard(row: ModelDashboardRow): ModelDashboard {
  return {
    ...row,
    metrics: row.metrics,
    budget: row.budget,
    session: row.session,
    parent: row.parent,
    _count: row._count,
  };
}

export function formatKeyMetrics(metrics: ModelMetric[]): ModelMetric[] {
  const holdout = metrics.filter((metric) => metric.split === "holdout");
  return holdout.length > 0
    ? holdout
    : metrics.filter((metric) => metric.split === "test");
}

export function formatMetricValue(value: ModelMetric["value"]): string {
  return `${(toNum(value) * 100).toFixed(1)}%`;
}

export function pickWinners(models: ModelDashboard[]): ModelDashboard[] {
  const latestByTier: Partial<Record<ModelTier, ModelDashboard>> = {};
  for (const model of models) {
    if (!model.promoted || model.promotedAt == null) continue;
    const incumbent = latestByTier[model.tier];
    if (
      !incumbent ||
      dateLikeToMs(model.promotedAt) > dateLikeToMs(incumbent.promotedAt)
    ) {
      latestByTier[model.tier] = model;
    }
  }
  return [ModelTier.cloud, ModelTier.edge]
    .map((tier) => latestByTier[tier])
    .filter((model): model is ModelDashboard => model != null);
}

function toBudgetNum(value: unknown): number {
  if (typeof value === "bigint") return Number(value);
  return toNum(value);
}

export function formatBudgetMetrics(
  budget: ModelBudget | null,
): ModelBudgetMetric[] {
  if (!budget) return [];
  const rows: ModelBudgetMetric[] = [
    {
      name: "flash",
      value: toBudgetNum(budget.flashKb),
      budget: toBudgetNum(budget.flashBudgetKb),
    },
    {
      name: "peakRam",
      value: toBudgetNum(budget.peakRamKb),
      budget: toBudgetNum(budget.peakRamBudgetKb),
    },
    {
      name: "macs",
      value: toBudgetNum(budget.macs),
      budget: toBudgetNum(budget.macsBudget),
    },
  ];
  if (budget.latencyMs != null) {
    rows.push({
      name: "latency",
      value: toBudgetNum(budget.latencyMs),
      budget: null,
    });
  }
  if (budget.energyMj != null) {
    rows.push({
      name: "energy",
      value: toBudgetNum(budget.energyMj),
      budget: null,
    });
  }
  if (budget.daysAutonomy != null) {
    rows.push({
      name: "autonomy",
      value: toBudgetNum(budget.daysAutonomy),
      budget: null,
    });
  }
  return rows;
}

export function formatBudgetValue(
  value: ModelBudgetMetric["value"],
  budget: ModelBudgetMetric["budget"],
  name: ModelBudgetMetricName,
): string {
  if (budget != null && budget > 0) {
    return `${((value / budget) * 100).toFixed(1)}%`;
  }
  switch (name) {
    case "flash":
    case "peakRam":
      return `${value.toFixed(1)} KB`;
    case "macs":
      return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
    case "latency":
      return `${value.toFixed(1)} ms`;
    case "energy":
      return `${value.toFixed(2)} mJ`;
    case "autonomy":
      return `${value.toFixed(1)} d`;
    default:
      return value.toFixed(1);
  }
}
