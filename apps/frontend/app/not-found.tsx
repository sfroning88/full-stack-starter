import Link from "next/link";
import { routes } from "@lib/routes";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-zinc-50 px-4 text-center dark:bg-black">
      <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
        Page not found
      </h1>
      <p className="max-w-md text-zinc-600 dark:text-zinc-400">
        Sorry, this page does not exist.
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
