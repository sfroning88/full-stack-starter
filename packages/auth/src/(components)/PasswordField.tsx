"use client";

import { useState } from "react";
import { Eye, EyeClosed } from "iconoir-react";
import { Input, Label } from "@fiery/ui";

type PasswordFieldProps = {
  id: string;
  name: string;
  label: string;
  minLength?: number;
};

export function PasswordField({
  id,
  name,
  label,
  minLength,
}: PasswordFieldProps) {
  const [show, setShow] = useState(false);
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        <Input
          id={id}
          name={name}
          type={show ? "text" : "password"}
          required
          minLength={minLength}
          className="w-full pr-10"
        />
        <button
          type="button"
          onClick={() => setShow((prev) => !prev)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          aria-label={show ? "Hide password" : "Show password"}
        >
          {show ? (
            <EyeClosed className="h-4 w-4" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
        </button>
      </div>
    </div>
  );
}
