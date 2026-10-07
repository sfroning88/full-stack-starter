"use client";

import type { Dispatch } from "react";
import type { UseMutationResult } from "@tanstack/react-query";
import { coerceIngestSource } from "@/lib/utils";
import type { AdminPanelAction, AdminPanelState } from "@/lib/reducers";
import { TEST_IDS } from "@lib/test-ids";
import {
  Button,
  Input,
  SectionLabel,
  SignalDropdown,
  SourceDropdown,
  StageDropdown,
} from "@fiery/ui";
import type {
  ApiJobsResponse,
  ApiPromoteResponse,
  ApiRefreshResponse,
  ApiRefineResponse,
  ApiTrainResponse,
  ModelDashboard,
} from "@fiery/types";
import { AdminMutationMessage } from "./AdminMutationMessage";

type AdminToolbarProps = {
  panel: AdminPanelState;
  dispatch: Dispatch<AdminPanelAction>;
  fieldClass: string;
  maxSamples: number | null;
  ingestSource: AdminPanelState["source"];
  lastModel: ModelDashboard | null;
  hasLastModel: boolean;
  ingestMutation: UseMutationResult<
    ApiJobsResponse,
    Error,
    { source: AdminPanelState["source"]; maxSamples: number | null }
  >;
  refineMutation: UseMutationResult<
    ApiRefineResponse,
    Error,
    { contractId: string; maxSamples: number | null }
  >;
  trainMutation: UseMutationResult<
    ApiTrainResponse,
    Error,
    {
      contractId: string;
      versionId: string;
      stage: AdminPanelState["stage"];
      parentId: string | null;
    }
  >;
  batchMutation: UseMutationResult<
    ApiJobsResponse,
    Error,
    { tier: ModelDashboard["tier"]; role: ModelDashboard["role"] }
  >;
  promoteMutation: UseMutationResult<ApiPromoteResponse, Error, void>;
  refreshMutation: UseMutationResult<
    ApiRefreshResponse,
    Error,
    { tier: ModelDashboard["tier"]; role: ModelDashboard["role"] }
  >;
};

export function AdminToolbar({
  panel,
  dispatch,
  fieldClass,
  maxSamples,
  ingestSource,
  lastModel,
  hasLastModel,
  ingestMutation,
  refineMutation,
  trainMutation,
  batchMutation,
  promoteMutation,
  refreshMutation,
}: AdminToolbarProps) {
  return (
    <>
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <SectionLabel>inputs</SectionLabel>
          <Input
            type="text"
            inputMode="numeric"
            data-testid={TEST_IDS.maxSamplesField}
            aria-label="Max samples"
            placeholder="Max samples"
            value={panel.maxSamples}
            onChange={(event) => {
              dispatch({
                type: "SET_MAX_SAMPLES",
                maxSamples: event.target.value,
              });
            }}
            className="w-28"
          />
          <SignalDropdown
            value={panel.signal}
            onChange={(signal) => {
              dispatch({ type: "SET_SIGNAL", signal });
            }}
            testId={TEST_IDS.signalField}
            className={fieldClass}
          />
          <SourceDropdown
            value={coerceIngestSource(panel.source)}
            onChange={(source) => {
              dispatch({ type: "SET_SOURCE", source });
            }}
            testId={TEST_IDS.sourceField}
            className={fieldClass}
          />
          <StageDropdown
            value={panel.stage}
            onChange={(stage) => {
              dispatch({ type: "SET_STAGE", stage });
            }}
            testId={TEST_IDS.stageField}
            className={fieldClass}
          />
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <SectionLabel>requests</SectionLabel>
          <Button
            data-testid={TEST_IDS.ingestButton}
            disabled={ingestMutation.isPending}
            onClick={() => {
              ingestMutation.mutate({
                source: ingestSource,
                maxSamples,
              });
            }}
          >
            {ingestMutation.isPending ? "Ingesting…" : "Ingest Samples"}
          </Button>
          <Button
            data-testid={TEST_IDS.refineButton}
            disabled={refineMutation.isPending || !hasLastModel}
            onClick={() => {
              if (!lastModel) return;
              refineMutation.mutate({
                contractId: lastModel.session.contract.id,
                maxSamples,
              });
            }}
          >
            {refineMutation.isPending ? "Refining…" : "Refine Shards"}
          </Button>
          <Button
            data-testid={TEST_IDS.trainButton}
            disabled={trainMutation.isPending || !hasLastModel}
            onClick={() => {
              if (!lastModel) return;
              trainMutation.mutate({
                contractId: lastModel.session.contract.id,
                versionId: lastModel.session.version.id,
                stage: panel.stage,
                parentId: lastModel.parentId,
              });
            }}
          >
            {trainMutation.isPending ? "Training…" : "Train Model"}
          </Button>
          <Button
            data-testid={TEST_IDS.batchButton}
            disabled={batchMutation.isPending || !hasLastModel}
            onClick={() => {
              if (!lastModel) return;
              batchMutation.mutate({
                tier: lastModel.tier,
                role: lastModel.role,
              });
            }}
          >
            {batchMutation.isPending ? "Caching…" : "Cache Inferences"}
          </Button>
          <Button
            data-testid={TEST_IDS.promoteButton}
            disabled={promoteMutation.isPending}
            onClick={() => promoteMutation.mutate()}
          >
            {promoteMutation.isPending ? "Evaluating…" : "Evaluate Models"}
          </Button>
          <Button
            data-testid={TEST_IDS.refreshButton}
            disabled={refreshMutation.isPending || !hasLastModel}
            onClick={() => {
              if (!lastModel) return;
              refreshMutation.mutate({
                tier: lastModel.tier,
                role: lastModel.role,
              });
            }}
          >
            {refreshMutation.isPending ? "Refreshing…" : "Refresh Model"}
          </Button>
        </div>
      </div>

      <AdminMutationMessage
        isError={ingestMutation.isError}
        isSuccess={ingestMutation.isSuccess}
        error={ingestMutation.error}
        fallbackError="Ingest request failed."
      >
        Ingest started — {ingestMutation.data?.jobIds.length} job(s) queued.
      </AdminMutationMessage>

      <AdminMutationMessage
        isError={refineMutation.isError}
        isSuccess={refineMutation.isSuccess}
        error={refineMutation.error}
        fallbackError="Refine request failed."
      >
        Refine started — {refineMutation.data?.jobIds.length} job(s) queued.
      </AdminMutationMessage>

      <AdminMutationMessage
        isError={trainMutation.isError}
        isSuccess={trainMutation.isSuccess}
        error={trainMutation.error}
        fallbackError="Training request failed."
      >
        Training started — {trainMutation.data?.jobIds.length} job(s) queued.
      </AdminMutationMessage>

      <AdminMutationMessage
        isError={batchMutation.isError}
        isSuccess={batchMutation.isSuccess}
        error={batchMutation.error}
        fallbackError="Batch request failed."
      >
        Batch started — {batchMutation.data?.jobIds.length} job(s) queued.
      </AdminMutationMessage>

      <AdminMutationMessage
        isError={promoteMutation.isError}
        isSuccess={promoteMutation.isSuccess}
        error={promoteMutation.error}
        fallbackError="Promote request failed."
      >
        Promote started — {promoteMutation.data?.evaluatedModels.length}{" "}
        model(s) evaluated.
      </AdminMutationMessage>

      <AdminMutationMessage
        isError={refreshMutation.isError}
        isSuccess={refreshMutation.isSuccess}
        error={refreshMutation.error}
        fallbackError="Refresh request failed."
      >
        Refresh started — model {refreshMutation.data?.artifactId} refreshed.
      </AdminMutationMessage>
    </>
  );
}
