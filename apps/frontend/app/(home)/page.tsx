import type { Metadata } from "next";
import { Suspense } from "react";
import Link from "next/link";
import { SignupButton } from "@/app/(components)/(privacy)/SignupButton";
import { LoginButton } from "@/app/(components)/(privacy)/LoginButton";
import { getSession } from "@my-project/auth/server";
import { AppUserProfileNotFoundError, UserService } from "@my-project/services";
import { MyProfileButton } from "@/app/(components)/(privacy)/MyProfileButton";
import { routes } from "@lib/routes";
import { TEST_IDS } from "@lib/test-ids";
import { type MyClass } from "@my-project/types";
import { fetchMessagesCached } from "@/lib/api/cache/home-cache";
import { HomeSkeleton } from "@/app/(components)/(home)/HomeSkeleton";
import { HomeAsync } from "@/app/(components)/(home)/HomeAsync";

export const metadata: Metadata = {
  title: "Home",
  description:
    "MyProject starter — backend message demo and cached message list.",
};

export default async function HomePage() {
  const { supabaseUser } = await getSession();
  let appUser = null;
  if (supabaseUser) {
    try {
      appUser = await UserService.ensureAppUserFromSupabaseAuth(supabaseUser);
    } catch (error) {
      if (error instanceof AppUserProfileNotFoundError) {
        appUser = null;
      } else {
        throw error;
      }
    }
  }
  const messagesPromise = fetchMessagesCached(
    supabaseUser ? supabaseUser.id : "anonymous",
  ).catch((): MyClass[] => []);

  const canSendMessage = Boolean(supabaseUser && appUser);

  return (
    <div className="flex flex-col gap-6" data-testid={TEST_IDS.homeScreen}>
      <h1
        data-testid={TEST_IDS.homeMessagesHeading}
        className="text-lg font-semibold text-myproject-black sm:text-2xl"
      >
        MyProject
      </h1>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Load messages from the database or enqueue a backend job at{" "}
        <code className="text-xs">/api/message</code>.
      </p>
      <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
        <div>
          {supabaseUser && appUser ? (
            <div className="mt-1 flex items-center gap-3">
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                {appUser.name} · {appUser.email}
              </p>
              <MyProfileButton userId={supabaseUser.id} />
            </div>
          ) : (
            <div className="mt-1 flex flex-wrap items-center gap-3">
              <SignupButton defaultEmail={supabaseUser?.email ?? undefined} />
              <LoginButton defaultEmail={supabaseUser?.email ?? undefined} />
            </div>
          )}
        </div>
        {appUser && appUser.isPlatformAdmin ? (
          <Link
            href={routes.admin.root}
            data-testid={TEST_IDS.openAdminLink}
            className="inline-flex w-fit shrink-0 text-sm font-medium text-zinc-900 underline underline-offset-4 dark:text-zinc-100"
          >
            Open admin
          </Link>
        ) : null}
      </div>
      <Suspense fallback={<HomeSkeleton />}>
        <HomeAsync
          initialMessagesPromise={messagesPromise}
          canSendMessage={canSendMessage}
        />
      </Suspense>
    </div>
  );
}
