-- gen_random_uuid() requires pgcrypto
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "iam";

-- CreateTable
CREATE TABLE IF NOT EXISTS "iam"."users" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "phone" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT false,
    "is_platform_admin" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "users_email_key" ON "iam"."users"("email");

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "users_phone_key" ON "iam"."users"("phone");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_users_is_active" ON "iam"."users"("is_active");
