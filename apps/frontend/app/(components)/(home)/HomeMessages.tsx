"use client";

import { TEST_IDS } from "@lib/test-ids";
import { type MyClass } from "@my-project/types";

type HomeMessagesProps = {
  messages: readonly MyClass[];
};

export function HomeMessages({ messages }: HomeMessagesProps) {
  return (
    <section
      data-testid={TEST_IDS.homeMessages}
      className="rounded-md border border-myproject-gray-200 bg-white/80 p-4 dark:border-white/10 dark:bg-surface-dark"
    >
      <h2 className="text-sm font-medium text-myproject-black dark:text-myproject-white">
        Messages
      </h2>
      {messages.length === 0 ? (
        <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">
          No messages yet.
        </p>
      ) : (
        <ul className="mt-3 space-y-2">
          {messages.map((item) => (
            <li
              key={item.id}
              className="rounded border border-myproject-gray-100 px-3 py-2 text-sm dark:border-white/10"
            >
              <p className="font-mono text-xs text-zinc-500 dark:text-zinc-400">
                {item.id}
              </p>
              <p className="mt-1 text-zinc-900 dark:text-zinc-100">
                {item.message ?? "—"}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
