"use client";

import { useCallback, useState } from "react";
import { createPortal } from "react-dom";
import { User, X } from "lucide-react";
import { useMyProfile } from "@/app/(hooks)/use-my-profile";
import { useModalFocus } from "@/app/(hooks)/use-modal-focus";
import { TEST_IDS } from "@lib/test-ids";

type MyProfileButtonProps = {
  userId: string;
};

export function MyProfileButton({ userId }: MyProfileButtonProps) {
  const [open, setOpen] = useState(false);
  const close = useCallback(() => setOpen(false), []);
  const dialogRef = useModalFocus(open, close);
  const { data: profile, isLoading } = useMyProfile(userId);

  const modal =
    open && typeof document !== "undefined" ? (
      <>
        <div
          className="fixed inset-0 z-100 bg-black/50"
          onClick={close}
          aria-hidden
        />
        <div
          ref={dialogRef}
          tabIndex={-1}
          className="fixed left-1/2 top-1/2 z-110 w-[min(90vw,400px)] -translate-x-1/2 -translate-y-1/2 rounded-sm border border-border bg-card p-5 shadow-lg outline-none"
          role="dialog"
          aria-modal
          aria-labelledby="profile-title"
          data-testid={TEST_IDS.myProfileDialog}
        >
          <div className="flex items-center justify-between gap-3">
            <h2
              id="profile-title"
              className="text-base font-semibold text-card-foreground"
            >
              My Profile
            </h2>
            <button
              type="button"
              data-testid={TEST_IDS.myProfileCloseButton}
              onClick={close}
              className="p-1 -mr-1 text-muted-foreground hover:text-card-foreground transition-colors"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {isLoading ? (
            <p className="mt-4 text-sm text-muted-foreground">Loading…</p>
          ) : profile ? (
            <dl className="mt-4 flex flex-col gap-3 text-sm">
              <div data-testid={TEST_IDS.myProfileNameField}>
                <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Name
                </dt>
                <dd className="mt-0.5 text-card-foreground">
                  {profile.name ?? "—"}
                </dd>
              </div>
              <div data-testid={TEST_IDS.myProfileEmailField}>
                <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Email
                </dt>
                <dd className="mt-0.5 text-card-foreground">
                  {profile.email ?? "—"}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Role
                </dt>
                <dd className="mt-0.5 text-card-foreground">
                  {profile.isPlatformAdmin ? "Admin" : "Member"}
                </dd>
              </div>
            </dl>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">
              Could not load profile.
            </p>
          )}
        </div>
      </>
    ) : null;

  return (
    <>
      <button
        type="button"
        data-testid={TEST_IDS.myProfileButton}
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-1.5 rounded-sm border border-border px-2.5 py-1.5 text-sm font-medium text-zinc-600 hover:bg-secondary hover:text-zinc-900 transition-colors dark:text-zinc-400 dark:hover:text-zinc-100"
      >
        <User className="h-3.5 w-3.5" aria-hidden />
        My Profile
      </button>
      {typeof window !== "undefined" && modal
        ? createPortal(modal, document.body)
        : null}
    </>
  );
}
