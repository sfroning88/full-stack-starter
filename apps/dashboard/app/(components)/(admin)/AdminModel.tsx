"use client";

import {
  Badge,
  SectionLabel,
  metricLabel,
  budgetLabel,
  tierColors,
  tierLabel,
  roleColors,
  roleLabel,
  signalColors,
  signalLabel,
} from "@fiery/ui";
import {
  formatDateTime,
  formatKeyMetrics,
  formatMetricValue,
  formatBudgetMetrics,
  formatBudgetValue,
} from "@fiery/utils";
import { Trophy } from "lucide-react";
import type { ModelDashboard } from "@fiery/types";

type AdminModelProps = {
  model: ModelDashboard;
  isMobile: boolean;
  showTrophy?: boolean;
};

export function AdminModel({ model, isMobile, showTrophy }: AdminModelProps) {
  const tier = model.tier;
  const role = model.role;
  const signal = model.session.signal;
  const metrics = formatKeyMetrics(model.metrics);
  const budgets = formatBudgetMetrics(model.budget);
  const trainedAt = model.session.finishedAt ?? model.createdAt;
  const metaText = isMobile ? "text-[11px]" : "text-xs";

  return (
    <li className="border-b border-white/5 last:border-0 px-3 md:px-5 py-3 md:py-4 transition-colors hover:bg-white/2">
      <div className="min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          {showTrophy ? (
            <Trophy
              className={`shrink-0 text-amber-400 ${isMobile ? "h-4 w-4" : "h-5 w-5"}`}
              aria-hidden
            />
          ) : null}
          <p
            className={`font-data-mono font-semibold text-white truncate ${isMobile ? "text-sm" : "text-base"}`}
          >
            {model.id}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`inline-flex items-center rounded-sm border px-2 py-0.5 font-data font-medium ${isMobile ? "text-xs" : "text-sm"} ${tierColors[tier]}`}
          >
            {tierLabel[tier]}
          </span>
          <span
            className={`inline-flex items-center rounded-sm border px-2 py-0.5 font-data font-medium ${isMobile ? "text-xs" : "text-sm"} ${roleColors[role]}`}
          >
            {roleLabel[role]}
          </span>
          <span
            className={`inline-flex items-center rounded-sm border px-2 py-0.5 font-data font-medium ${isMobile ? "text-xs" : "text-sm"} ${signalColors[signal]}`}
          >
            {signalLabel[signal]}
          </span>
        </div>
        <div
          className={`mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-white/50 ${metaText}`}
        >
          <SectionLabel>trained at</SectionLabel>
          <span>{formatDateTime(trainedAt)}</span>
        </div>
        <div
          className={`mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-white/50 ${metaText}`}
        >
          <SectionLabel>architecture</SectionLabel>
          <span>{model.architecture}</span>
        </div>
        {model.parent ? (
          <div
            className={`mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-white/50 ${metaText}`}
          >
            <SectionLabel>parent</SectionLabel>
            <span>{model.parentId}</span>
          </div>
        ) : null}
        <div
          className={`mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 ${metaText}`}
        >
          <SectionLabel>scores</SectionLabel>
          {metrics.map((metric) => (
            <Badge colorScheme="dark" key={`${metric.split}-${metric.name}`}>
              {metricLabel[metric.name]} {formatMetricValue(metric.value)}
            </Badge>
          ))}
        </div>
        {budgets.length > 0 ? (
          <div
            className={`mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 ${metaText}`}
          >
            <SectionLabel>budget</SectionLabel>
            {budgets.map((row) => (
              <Badge colorScheme="dark" key={row.name}>
                {budgetLabel[row.name]}{" "}
                {formatBudgetValue(row.value, row.budget, row.name)}
              </Badge>
            ))}
          </div>
        ) : null}
      </div>
    </li>
  );
}
