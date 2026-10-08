"use server";

import { z } from "zod";
import { platformAdminAction } from "@my-project/auth/server";
import { AdminService } from "@lib/services";
import { type ApiJobsResponse, type MyClass } from "@my-project/types";

const adminService = new AdminService();

const messageSchema = z.void();

export const messageAction = platformAdminAction(
  messageSchema,
  async (ctx): Promise<ApiJobsResponse> => {
    return await adminService.message(ctx);
  },
);

const fetchMessagesSchema = z.void();

export const fetchMessagesAction = platformAdminAction(
  fetchMessagesSchema,
  async (): Promise<MyClass[]> => {
    return await adminService.fetchMessages();
  },
);
