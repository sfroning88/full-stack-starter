"use server";

import { z } from "zod";
import { createPublicAction, selfUserAction } from "@my-project/auth/server";
import { HomeService } from "@lib/services";
import { type ApiJobsResponse, type MyClass } from "@my-project/types";

const homeService = new HomeService();

const messageSchema = z.void();

export const messageAction = selfUserAction(
  messageSchema,
  async (ctx): Promise<ApiJobsResponse> => {
    return await homeService.message(ctx);
  },
);

const fetchMessagesSchema = z.void();

export const fetchMessagesAction = createPublicAction(
  fetchMessagesSchema,
  async (): Promise<MyClass[]> => {
    return await homeService.fetchMessages();
  },
);
