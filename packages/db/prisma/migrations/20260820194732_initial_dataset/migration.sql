-- DropForeignKey
ALTER TABLE "ai"."training_session" DROP CONSTRAINT "training_session_contract_id_fkey";

-- AlterTable
ALTER TABLE "ai"."training_session" ADD COLUMN     "version_id" UUID NOT NULL;

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."dataset_ingest" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "source" "ai"."training_sample_source" NOT NULL,
    "asset_count" INTEGER NOT NULL DEFAULT 0,
    "status" "ai"."training_status" NOT NULL,
    "started_at" TIMESTAMPTZ(6),
    "finished_at" TIMESTAMPTZ(6),
    "error_message" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "dataset_ingest_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."dataset_version" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "transform_hash" TEXT NOT NULL,
    "manifest_path" TEXT NOT NULL,
    "shard_count" INTEGER NOT NULL,
    "sample_count" INTEGER NOT NULL,
    "status" "ai"."training_status" NOT NULL,
    "contract_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "dataset_version_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_dataset_ingest_by_source" ON "ai"."dataset_ingest"("source", "status");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_dataset_version_by_transform_hash" ON "ai"."dataset_version"("transform_hash", "created_at" DESC);

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "dataset_version_contract_id_transform_hash_key" ON "ai"."dataset_version"("contract_id", "transform_hash");

-- AddForeignKey
ALTER TABLE "ai"."dataset_version" ADD CONSTRAINT "dataset_version_contract_id_fkey" FOREIGN KEY ("contract_id") REFERENCES "ai"."training_contract"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_session" ADD CONSTRAINT "training_session_contract_id_fkey" FOREIGN KEY ("contract_id") REFERENCES "ai"."training_contract"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_session" ADD CONSTRAINT "training_session_version_id_fkey" FOREIGN KEY ("version_id") REFERENCES "ai"."dataset_version"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
