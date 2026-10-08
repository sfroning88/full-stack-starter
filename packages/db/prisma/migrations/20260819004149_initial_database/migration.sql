-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "ai";

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."my_class" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "message" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
);
