-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "mlflow";

-- AlterTable
ALTER TABLE "ai"."model_artifact" ADD COLUMN     "hf_repo_id" TEXT,
ADD COLUMN     "hf_revision" TEXT,
ADD COLUMN     "mlflow_run_id" TEXT;
