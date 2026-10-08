"use client";

import { EMPTY_MESSAGES } from "@/lib/constants";
import { useFetchAdminMessages } from "@/app/(hooks)/use-fetch-messages";
import { useAdminMessage } from "@/app/(hooks)/use-message";
import { useUserId } from "@/app/(hooks)/use-user-id";
import { type MyClass } from "@my-project/types";
import { AdminMessages } from "./AdminMessages";
import { AdminToolbar } from "./AdminToolbar";

type AdminPanelProps = {
  initialMessages?: MyClass[];
};

export function AdminPanel({ initialMessages }: AdminPanelProps) {
  const userId = useUserId();
  const {
    data: messages,
    isLoading,
    isError,
    error,
  } = useFetchAdminMessages(userId, initialMessages);
  const messageMutation = useAdminMessage(userId);

  const listed = messages ?? EMPTY_MESSAGES;

  return (
    <div className="space-y-4 font-data">
      <AdminToolbar messageMutation={messageMutation} />
      {isLoading ? (
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Loading messages…
        </p>
      ) : isError ? (
        <p className="text-sm text-red-600 dark:text-red-400">
          {error instanceof Error ? error.message : "Could not load messages."}
        </p>
      ) : (
        <AdminMessages messages={listed} />
      )}
    </div>
  );
}
