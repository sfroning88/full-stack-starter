"use client";

import { useEffect, useReducer } from "react";
import { useMediaQuery } from "@/app/(hooks)/use-media-query";
import { useFetchModels } from "@/app/(hooks)/use-fetch-models";
import { useFetchWinners } from "@/app/(hooks)/use-fetch-winners";
import { useIngest } from "@/app/(hooks)/use-ingest";
import { useRefine } from "@/app/(hooks)/use-refine";
import { useTrain } from "@/app/(hooks)/use-train";
import { useBatch } from "@/app/(hooks)/use-batch";
import { usePromote } from "@/app/(hooks)/use-promote";
import { useRefresh } from "@/app/(hooks)/use-refresh";
import { useUserId } from "@/app/(hooks)/use-user-id";
import { MOBILE_BREAKPOINT, EMPTY_MODELS } from "@/lib/constants";
import { coerceIngestSource } from "@/lib/utils";
import { adminReducer, adminPanelInitialState } from "@/lib/reducers";
import { dateLikeToMs, formatNullableInt } from "@fiery/utils";
import { ModelDashboard, TrainingSignal } from "@fiery/types";
import { AdminToolbar } from "./AdminToolbar";
import { AdminCatalog } from "./AdminCatalog";

type AdminPanelProps = {
  initialWinners?: ModelDashboard[];
  initialModels?: ModelDashboard[];
};

export function AdminPanel({ initialWinners, initialModels }: AdminPanelProps) {
  const userId = useUserId();
  const isMobile = !useMediaQuery(`(min-width: ${MOBILE_BREAKPOINT}px)`, true);

  const [panel, dispatch] = useReducer(adminReducer, adminPanelInitialState);

  const {
    data: winnersData,
    isLoading: winnersLoading,
    isError: winnersError,
    error: winnersErrorDetail,
  } = useFetchWinners(userId, initialWinners);

  const {
    data: allModels,
    isLoading: allModelsLoading,
    isError: allModelsError,
    error: allModelsErrorDetail,
  } = useFetchModels(userId, initialModels);

  const ingestMutation = useIngest(userId);
  const refineMutation = useRefine(userId);
  const trainMutation = useTrain(userId);
  const batchMutation = useBatch(userId);
  const promoteMutation = usePromote(userId);
  const refreshMutation = useRefresh(userId);

  useEffect(() => {
    ingestMutation.reset();
    refineMutation.reset();
    trainMutation.reset();
    batchMutation.reset();
    promoteMutation.reset();
    refreshMutation.reset();
  }, []);

  const maxSamples = formatNullableInt(panel.maxSamples);
  const ingestSource = coerceIngestSource(panel.source);

  const models = allModels ?? EMPTY_MODELS;
  const winners = winnersData ?? EMPTY_MODELS;
  const winnerIds = new Set(winners.map((model) => model.id));
  const remainingModels = panel.loadAll
    ? [...models]
        .filter((model) => !winnerIds.has(model.id))
        .sort((modelA, modelB) => {
          if (modelA.promoted !== modelB.promoted) {
            return modelA.promoted ? -1 : 1;
          }
          return (
            dateLikeToMs(modelB.createdAt) - dateLikeToMs(modelA.createdAt)
          );
        })
    : [];

  let lastDeformationModel: ModelDashboard | null = null;
  let lastSeismicModel: ModelDashboard | null = null;

  for (const model of models) {
    switch (model.session.signal) {
      case TrainingSignal.deformation:
        if (
          !lastDeformationModel ||
          dateLikeToMs(model.createdAt) >
            dateLikeToMs(lastDeformationModel.createdAt)
        ) {
          lastDeformationModel = model;
        }
        break;
      case TrainingSignal.seismic:
        if (
          !lastSeismicModel ||
          dateLikeToMs(model.createdAt) >
            dateLikeToMs(lastSeismicModel.createdAt)
        ) {
          lastSeismicModel = model;
        }
        break;
    }
  }

  const lastModel =
    panel.signal === TrainingSignal.deformation
      ? lastDeformationModel
      : lastSeismicModel;
  const hasLastModel = lastModel != null;
  const fieldClass = isMobile ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm";

  return (
    <div className="space-y-4 font-data">
      <AdminToolbar
        panel={panel}
        dispatch={dispatch}
        fieldClass={fieldClass}
        maxSamples={maxSamples}
        ingestSource={ingestSource}
        lastModel={lastModel}
        hasLastModel={hasLastModel}
        ingestMutation={ingestMutation}
        refineMutation={refineMutation}
        trainMutation={trainMutation}
        batchMutation={batchMutation}
        promoteMutation={promoteMutation}
        refreshMutation={refreshMutation}
      />
      <AdminCatalog
        isMobile={isMobile}
        winnersLoading={winnersLoading}
        winnersError={winnersError}
        winnersErrorDetail={winnersErrorDetail}
        winners={winners}
        loadAll={panel.loadAll}
        onLoadAll={() => dispatch({ type: "SET_LOAD_ALL", loadAll: true })}
        allModelsLoading={allModelsLoading}
        allModelsError={allModelsError}
        allModelsErrorDetail={allModelsErrorDetail}
        remainingModels={remainingModels}
      />
    </div>
  );
}
