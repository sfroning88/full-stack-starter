import { ZodSchema } from "zod";
import { requireUser, requirePlatformAdmin } from "./auth-guards";

export type SafeAction<Input, Output> = (input: Input) => Promise<Output>;

export function createPublicAction<Input, Output>(
  schema: ZodSchema<Input>,
  handler: (ctx: { input: Input }) => Promise<Output>,
): SafeAction<Input, Output> {
  return async (raw: unknown) => {
    const parsed = schema.parse(raw);
    return handler({ input: parsed });
  };
}

export function selfUserAction<Input, Output>(
  schema: ZodSchema<Input>,
  handler: (ctx: Input & { userId: string }) => Promise<Output>,
): SafeAction<Input, Output> {
  return async (raw: unknown) => {
    const { supabaseUser } = await requireUser();
    const parsed = schema.parse(raw);
    return handler({ ...parsed, userId: supabaseUser.id });
  };
}

export function platformAdminAction<Input, Output>(
  schema: ZodSchema<Input>,
  handler: (ctx: Input & { userId: string }) => Promise<Output>,
): SafeAction<Input, Output> {
  return async (raw: unknown) => {
    const { appUser } = await requirePlatformAdmin();
    const parsed = schema.parse(raw);
    return handler({ ...parsed, userId: appUser.id });
  };
}
