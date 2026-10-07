"use server";

import { z } from "zod";
import { createPublicAction } from "@fiery/auth/server";
import { readFile } from "fs/promises";
import { join } from "path";
import { PRIVACY_DOC_PATH } from "@/lib/constants";

const getPrivacyContentSchema = z.object({});

export const getPrivacyContentAction = createPublicAction(
  getPrivacyContentSchema,
  async () => {
    const filePath = join(process.cwd(), PRIVACY_DOC_PATH);
    const content = await readFile(filePath, "utf-8");
    return content;
  },
);
