"use client";

import { TEST_IDS } from "@lib/test-ids";
import { type UseMutationResult } from "@tanstack/react-query";
import { type ApiJobsResponse } from "@my-project/types";

type AdminToolbarProps = {
  messageMutation: UseMutationResult<ApiJobsResponse, Error, void, unknown>;
};

export function AdminToolbar({ messageMutation }: AdminToolbarProps) {
  const { isPending, isError, isSuccess, error, data, mutate } =
    messageMutation;

  return (
    <div
      className="space-y-3 rounded-md border border-myproject-gray-200 bg-white/80 p-4 dark:border-white/10 dark:bg-surface-dark"
      data-testid={TEST_IDS.adminToolbar}
    >
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        POST to the backend <code className="text-xs">/api/message</code> job
        endpoint (admin-only).
      </p>
      <button
        type="button"
        data-testid={TEST_IDS.adminMessageButton}
        disabled={isPending}
        onClick={() => mutate()}
        className="inline-flex items-center justify-center rounded-md border border-myproject-black bg-myproject-black px-4 py-2 text-sm font-medium text-myproject-white disabled:cursor-not-allowed disabled:opacity-50 dark:border-myproject-white dark:bg-myproject-white dark:text-myproject-black"
      >
        {isPending ? "Sending…" : "Send backend message"}
      </button>
      {isError ? (
        <p className="text-sm text-red-600 dark:text-red-400">
          {error instanceof Error ? error.message : "Could not send message."}
        </p>
      ) : null}
      {isSuccess && data ? (
        <p className="text-sm text-myproject-gray-700 dark:text-myproject-gray-200">
          Queued {data.jobIds.length} job(s).
        </p>
      ) : null}
    </div>
  );
}
