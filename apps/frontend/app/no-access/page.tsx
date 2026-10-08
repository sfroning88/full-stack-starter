import type { Metadata } from "next";
import Link from "next/link";
import { routes } from "@lib/routes";

export const metadata: Metadata = {
  title: "No Access",
  description: "You do not have permission to view this page.",
  robots: { index: false, follow: false },
};

export default function NoAccessPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-zinc-50 px-4 text-center dark:bg-black">
      <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
        No access
      </h1>
      <p className="max-w-md text-zinc-600 dark:text-zinc-400">
        Sorry, you don&apos;t have permission to view this page.
      </p>
      <Link
        href={routes.root}
        className="text-sm font-medium text-zinc-900 underline underline-offset-4 dark:text-zinc-100"
      >
        Go home
      </Link>
    </div>
  );
}
