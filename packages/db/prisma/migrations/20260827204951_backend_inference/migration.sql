-- CreateEnum
CREATE TYPE "ai"."inference_abstain_reason" AS ENUM ('low_coherence', 'low_snr', 'transform_rejected', 'contract_mismatch', 'low_confidence');

-- DropForeignKey
ALTER TABLE "ai"."prediction_deformation" DROP CONSTRAINT "prediction_deformation_artifact_id_fkey";

-- DropForeignKey
ALTER TABLE "ai"."prediction_deformation" DROP CONSTRAINT "prediction_deformation_interferogram_id_fkey";

-- DropForeignKey
ALTER TABLE "ai"."prediction_seismic" DROP CONSTRAINT "prediction_seismic_artifact_id_fkey";

-- DropForeignKey
ALTER TABLE "ai"."prediction_seismic" DROP CONSTRAINT "prediction_seismic_seismic_event_id_fkey";

-- AlterTable
ALTER TABLE "ai"."dataset_version" ALTER COLUMN "transform_hash" SET DATA TYPE VARCHAR(64);

-- DropTable
DROP TABLE IF EXISTS "ai"."prediction_deformation";

-- DropTable
DROP TABLE IF EXISTS "ai"."prediction_seismic";

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."inference_deformation" (
    "score" DECIMAL(6,5),
    "label" "ai"."training_deformation_label",
    "threshold_used" DECIMAL(6,5) NOT NULL,
    "abstention_band" DECIMAL(6,5) NOT NULL,
    "abstained" BOOLEAN NOT NULL DEFAULT false,
    "abstained_reason" "ai"."inference_abstain_reason",
    "transform_hash" VARCHAR(64) NOT NULL,
    "op_version" INTEGER NOT NULL,
    "latency_ms" DECIMAL(10,3),
    "inferred_at" TIMESTAMPTZ(6) NOT NULL,
    "artifact_id" UUID NOT NULL,
    "interferogram_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "inference_deformation_pkey" PRIMARY KEY ("artifact_id","interferogram_id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."inference_seismic" (
    "label" "ai"."training_seismic_label",
    "probabilities" DECIMAL(6,5)[],
    "class_order" "ai"."training_seismic_label"[],
    "threshold_used" DECIMAL(6,5) NOT NULL,
    "abstention_band" DECIMAL(6,5) NOT NULL,
    "abstained" BOOLEAN NOT NULL DEFAULT false,
    "abstained_reason" "ai"."inference_abstain_reason",
    "transform_hash" VARCHAR(64) NOT NULL,
    "op_version" INTEGER NOT NULL,
    "latency_ms" DECIMAL(10,3),
    "inferred_at" TIMESTAMPTZ(6) NOT NULL,
    "artifact_id" UUID NOT NULL,
    "seismic_event_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "inference_seismic_pkey" PRIMARY KEY ("artifact_id","seismic_event_id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."inference_feedback" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "agreed" BOOLEAN NOT NULL,
    "corrected_deformation" "ai"."training_deformation_label",
    "corrected_seismic" "ai"."training_seismic_label",
    "note" TEXT,
    "interferogram_id" UUID,
    "seismic_event_id" UUID,
    "user_id" UUID,
    "artifact_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "inference_feedback_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_deformation_by_interferogram" ON "ai"."inference_deformation"("interferogram_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_deformation_by_artifact" ON "ai"."inference_deformation"("interferogram_id", "artifact_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_deformation_abstained" ON "ai"."inference_deformation"("artifact_id", "abstained");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_deformation_abstained_reason" ON "ai"."inference_deformation"("artifact_id", "abstained_reason");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_deformation_recency" ON "ai"."inference_deformation"("created_at" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_deformation_by_label" ON "ai"."inference_deformation"("label", "score" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_seismic_by_event" ON "ai"."inference_seismic"("seismic_event_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_seismic_by_artifact" ON "ai"."inference_seismic"("seismic_event_id", "artifact_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_seismic_abstained" ON "ai"."inference_seismic"("artifact_id", "abstained");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_seismic_abstained_reason" ON "ai"."inference_seismic"("artifact_id", "abstained_reason");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_seismic_recency" ON "ai"."inference_seismic"("created_at" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_seismic_by_label" ON "ai"."inference_seismic"("label");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_feedback_by_user" ON "ai"."inference_feedback"("user_id");

-- AddForeignKey
ALTER TABLE "ai"."inference_deformation" ADD CONSTRAINT "inference_deformation_artifact_id_fkey" FOREIGN KEY ("artifact_id") REFERENCES "ai"."model_artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."inference_deformation" ADD CONSTRAINT "inference_deformation_interferogram_id_fkey" FOREIGN KEY ("interferogram_id") REFERENCES "ai"."training_interferogram"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."inference_seismic" ADD CONSTRAINT "inference_seismic_artifact_id_fkey" FOREIGN KEY ("artifact_id") REFERENCES "ai"."model_artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."inference_seismic" ADD CONSTRAINT "inference_seismic_seismic_event_id_fkey" FOREIGN KEY ("seismic_event_id") REFERENCES "ai"."training_seismic_event"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."inference_feedback" ADD CONSTRAINT "inference_feedback_artifact_id_interferogram_id_fkey" FOREIGN KEY ("artifact_id", "interferogram_id") REFERENCES "ai"."inference_deformation"("artifact_id", "interferogram_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."inference_feedback" ADD CONSTRAINT "inference_feedback_artifact_id_seismic_event_id_fkey" FOREIGN KEY ("artifact_id", "seismic_event_id") REFERENCES "ai"."inference_seismic"("artifact_id", "seismic_event_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."inference_feedback" ADD CONSTRAINT "inference_feedback_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "iam"."users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."inference_feedback" ADD CONSTRAINT "inference_feedback_artifact_id_fkey" FOREIGN KEY ("artifact_id") REFERENCES "ai"."model_artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- (manual) Add Constraint
ALTER TABLE ai.inference_deformation
  ADD CONSTRAINT deformation_abstain_consistency
  CHECK (abstained = (abstained_reason IS NOT NULL));

-- (manual) Add Constraint
ALTER TABLE ai.inference_deformation
  ADD CONSTRAINT deformation_abstain_nulls
  CHECK (abstained = (score IS NULL) AND abstained = (label IS NULL));

-- (manual) Add Constraint
ALTER TABLE ai.inference_deformation
  ADD CONSTRAINT deformation_reason_scope
  CHECK (abstained_reason IS NULL OR abstained_reason <> 'low_snr');

-- (manual) Add Constraint
ALTER TABLE ai.inference_seismic
  ADD CONSTRAINT seismic_abstain_consistency
  CHECK (abstained = (abstained_reason IS NOT NULL));

-- (manual) Add Constraint
ALTER TABLE ai.inference_seismic
  ADD CONSTRAINT seismic_abstain_nulls
  CHECK (abstained = (label IS NULL)
     AND abstained = (cardinality(probabilities) = 0));

-- (manual) Add Constraint
ALTER TABLE ai.inference_seismic
  ADD CONSTRAINT seismic_reason_scope
  CHECK (abstained_reason IS NULL OR abstained_reason <> 'low_coherence');

-- (manual) Add Constraint
ALTER TABLE ai.inference_seismic
  ADD CONSTRAINT seismic_class_order_cardinality
  CHECK (cardinality(probabilities) = cardinality(class_order));

-- (manual) Add Constraint
ALTER TABLE ai.inference_feedback
  ADD CONSTRAINT feedback_single_target
  CHECK ((interferogram_id IS NULL) <> (seismic_event_id IS NULL));

-- (manual) Add Constraint
ALTER TABLE ai.inference_feedback
  ADD CONSTRAINT feedback_corrected_scope
  CHECK ((corrected_deformation IS NULL OR interferogram_id IS NOT NULL)
     AND (corrected_seismic     IS NULL OR seismic_event_id IS NOT NULL));

-- (manual) Add Constraint
ALTER TABLE ai.inference_feedback
  ADD CONSTRAINT feedback_corrected_required
  CHECK (agreed
      OR corrected_deformation IS NOT NULL
      OR corrected_seismic     IS NOT NULL);

-- (manual) Create Unique Index
ALTER TABLE ai.inference_feedback
  ADD CONSTRAINT feedback_one_per_user_per_prediction
  UNIQUE NULLS NOT DISTINCT (artifact_id, interferogram_id, seismic_event_id, user_id);

