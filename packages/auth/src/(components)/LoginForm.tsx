"use client";

import { Input, Label } from "@fiery/ui";
import { useLogin } from "../(hooks)/use-login";
import { GoogleSso } from "./GoogleSso";
import { OutlookSso } from "./OutlookSso";
import { LoginSubmit } from "./LoginSubmit";

type LoginFormProps = {
  defaultEmail?: string;
  initialError?: string | null;
};

export function LoginForm({ defaultEmail, initialError }: LoginFormProps) {
  const { error, isLoading, handleSubmit } = useLogin(initialError);
  return (
    <form className="flex w-full flex-col gap-4" onSubmit={handleSubmit}>
      {error ? (
        <p className="text-sm font-semibold text-white" role="alert">
          {error}
        </p>
      ) : null}
      <div className="flex w-full flex-col gap-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          defaultValue={defaultEmail}
          placeholder="your@email.com"
          className="w-full"
        />
      </div>
      <div className="flex w-full flex-col gap-2">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          className="w-full"
        />
      </div>
      <LoginSubmit isLoading={isLoading} />
      <div className="relative my-2 flex items-center">
        <div className="grow border-t border-white" />
        <span className="mx-3 text-xs text-white/70">or</span>
        <div className="grow border-t border-white" />
      </div>
      <div className="flex w-full flex-col gap-2">
        <GoogleSso />
        <OutlookSso />
      </div>
    </form>
  );
}
