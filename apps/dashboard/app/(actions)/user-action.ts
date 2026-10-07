"use server";

import { z } from "zod";
import { db } from "@fiery/db";
import { selfUserAction } from "@fiery/auth/server";

const emptySchema = z.object({});

export const getMyProfileAction = selfUserAction(
  emptySchema,
  async ({ userId }) => {
    const user = await db.user.findUniqueOrThrow({
      where: { id: userId },
      select: { id: true, email: true, name: true, isPlatformAdmin: true },
    });
    return user;
  },
);
