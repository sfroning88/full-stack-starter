"use client";

import { Button, Input, Label } from "@fiery/ui";
import { PasswordField } from "./PasswordField";
import { useSignup } from "../(hooks)/use-signup";

type SignupFormProps = {
  defaultEmail?: string;
  initialError?: string | null;
};

export function SignupForm({ defaultEmail, initialError }: SignupFormProps) {
  const { error, isLoading, handleSubmit } = useSignup(initialError);
  return (
    <form className="flex w-full flex-col gap-4" onSubmit={handleSubmit}>
      {error ? (
        <p className="text-sm font-semibold text-white" role="alert">
          {error}
        </p>
      ) : null}
      <div className="flex flex-col gap-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          name="email"
          type="email"
          required
          defaultValue={defaultEmail}
          readOnly={Boolean(defaultEmail)}
          className="w-full"
        />
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="name">Username</Label>
        <Input
          id="name"
          name="name"
          type="text"
          required
          autoComplete="name"
          className="w-full"
        />
      </div>
      <PasswordField
        id="password"
        name="password"
        label="Password"
        minLength={6}
      />
      <PasswordField
        id="confirmPassword"
        name="confirmPassword"
        label="Confirm password"
        minLength={6}
      />
      <Button type="submit" disabled={isLoading} className="w-full">
        {isLoading ? "Creating account..." : "Complete registration"}
      </Button>
    </form>
  );
}
