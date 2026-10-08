"use client";

import { EMPTY_MESSAGES } from "@/lib/constants";
import { useFetchHomeMessages } from "@/app/(hooks)/use-fetch-messages";
import { useHomeMessage } from "@/app/(hooks)/use-message";
import { useUserId } from "@/app/(hooks)/use-user-id";
import { type MyClass } from "@my-project/types";
import { HomeMessages } from "./HomeMessages";
import { HomeToolbar } from "./HomeToolbar";

type HomePanelProps = {
  initialMessages?: MyClass[];
  canSendMessage: boolean;
};

export function HomePanel({ initialMessages, canSendMessage }: HomePanelProps) {
  const userId = useUserId();
  const {
    data: messages,
    isLoading,
    isError,
    error,
  } = useFetchHomeMessages(userId, initialMessages);
  const messageMutation = useHomeMessage(userId);

  const listed = messages ?? EMPTY_MESSAGES;

  return (
    <div className="space-y-4 font-data">
      <HomeToolbar
        canSendMessage={canSendMessage}
        messageMutation={messageMutation}
      />
      {isLoading ? (
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Loading messages…
        </p>
      ) : isError ? (
        <p className="text-sm text-red-600 dark:text-red-400">
          {error instanceof Error ? error.message : "Could not load messages."}
        </p>
      ) : (
        <HomeMessages messages={listed} />
      )}
    </div>
  );
}
