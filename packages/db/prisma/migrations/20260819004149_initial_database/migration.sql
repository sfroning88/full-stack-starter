-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "ai";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "geo";

-- CreateEnum
CREATE TYPE "ai"."model_tier" AS ENUM ('cloud', 'edge');

-- CreateEnum
CREATE TYPE "ai"."model_role" AS ENUM ('screener', 'teacher', 'student');

-- CreateEnum
CREATE TYPE "ai"."model_metric_name" AS ENUM ('accuracy', 'recall', 'precision', 'abstention_rate', 'f1_score', 'macro_f1_score');

-- CreateEnum
CREATE TYPE "ai"."training_split" AS ENUM ('train', 'validate', 'test', 'holdout');

-- CreateEnum
CREATE TYPE "ai"."training_sample_source" AS ENUM ('hephaestus', 'licsar', 'okada', 'llaima', 'villarrica');

-- CreateEnum
CREATE TYPE "ai"."training_signal" AS ENUM ('deformation', 'seismic');

-- CreateEnum
CREATE TYPE "ai"."training_stage" AS ENUM ('pretrain', 'lora', 'distill', 'prune', 'quantize');

-- CreateEnum
CREATE TYPE "ai"."training_status" AS ENUM ('pending', 'executing', 'completed', 'failed', 'cancelled');

-- CreateEnum
CREATE TYPE "ai"."training_precision" AS ENUM ('fp32', 'fp16', 'int8');

-- CreateEnum
CREATE TYPE "ai"."training_seismic_label" AS ENUM ('vt', 'lp', 'tr', 'tc');

-- CreateEnum
CREATE TYPE "ai"."training_deformation_label" AS ENUM ('positive', 'negative', 'uncertain');

-- CreateEnum
CREATE TYPE "ai"."training_window" AS ENUM ('hann', 'hamming', 'blackman', 'boxcar', 'tukey');

-- CreateEnum
CREATE TYPE "ai"."training_normalize" AS ENUM ('minmax', 'zscore', 'percentile', 'none');

-- CreateEnum
CREATE TYPE "ai"."training_optimizer" AS ENUM ('adam', 'adamw', 'sgd', 'rmsprop');

-- CreateEnum
CREATE TYPE "ai"."training_rate_schedule" AS ENUM ('constant', 'cosine', 'step', 'linear', 'warmup_cosine');

-- CreateEnum
CREATE TYPE "ai"."training_sparsity_schedule" AS ENUM ('linear', 'cubic', 'one_shot');

-- CreateEnum
CREATE TYPE "ai"."training_pruning_criterion" AS ENUM ('l1_magnitude', 'l2_magnitude', 'random', 'movement');

-- CreateEnum
CREATE TYPE "ai"."training_quantize_method" AS ENUM ('ptq', 'qat');

-- CreateEnum
CREATE TYPE "ai"."training_deformation_source_type" AS ENUM ('mogi', 'okada');

-- CreateEnum
CREATE TYPE "ai"."training_noise_model" AS ENUM ('none', 'atmospheric', 'turbulent');

-- CreateEnum
CREATE TYPE "geo"."volcano_zone" AS ENUM ('svz', 'cvz', 'nvz', 'avz', 'other');

-- CreateEnum
CREATE TYPE "geo"."volcano_activity_source" AS ENUM ('gvp', 'sernageomin', 'manual');

-- CreateEnum
CREATE TYPE "geo"."volcano_alert_level" AS ENUM ('green', 'yellow', 'orange', 'red');

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."model_artifact" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tier" "ai"."model_tier" NOT NULL,
    "role" "ai"."model_role" NOT NULL,
    "stage" "ai"."training_stage" NOT NULL,
    "precision" "ai"."training_precision" NOT NULL DEFAULT 'fp32',
    "architecture" TEXT NOT NULL,
    "param_count" INTEGER NOT NULL,
    "sparsity" DECIMAL(4,3) NOT NULL DEFAULT 0,
    "storage_path" TEXT NOT NULL,
    "signature" TEXT NOT NULL,
    "signed_at" TIMESTAMPTZ(6) NOT NULL,
    "promoted" BOOLEAN NOT NULL DEFAULT false,
    "promoted_at" TIMESTAMPTZ(6),
    "session_id" UUID NOT NULL,
    "parent_id" UUID,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "model_artifact_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."model_metric" (
    "name" "ai"."model_metric_name" NOT NULL,
    "split" "ai"."training_split" NOT NULL,
    "value" DECIMAL(8,5) NOT NULL,
    "artifact_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "model_metric_pkey" PRIMARY KEY ("artifact_id","split","name")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."model_budget" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "flash_kb" DECIMAL(10,2) NOT NULL,
    "flash_budget_kb" DECIMAL(10,2) NOT NULL,
    "peak_ram_kb" DECIMAL(10,2) NOT NULL,
    "peak_ram_budget_kb" DECIMAL(10,2) NOT NULL,
    "macs" BIGINT NOT NULL,
    "macs_budget" BIGINT NOT NULL,
    "latency_ms" DECIMAL(10,3),
    "energy_mj" DECIMAL(12,4),
    "days_autonomy" DECIMAL(8,2),
    "passed" BOOLEAN NOT NULL,
    "checked_at" TIMESTAMPTZ(6) NOT NULL,
    "artifact_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "model_budget_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."prediction_deformation" (
    "score" DECIMAL(6,5) NOT NULL,
    "label" "ai"."training_deformation_label" NOT NULL,
    "abstained" BOOLEAN NOT NULL DEFAULT false,
    "inferred_at" TIMESTAMPTZ(6) NOT NULL,
    "artifact_id" UUID NOT NULL,
    "interferogram_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "prediction_deformation_pkey" PRIMARY KEY ("artifact_id","interferogram_id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."prediction_seismic" (
    "label" "ai"."training_seismic_label" NOT NULL,
    "probabilities" DECIMAL(6,5)[],
    "latency_ms" DECIMAL(10,3),
    "inferred_at" TIMESTAMPTZ(6) NOT NULL,
    "artifact_id" UUID NOT NULL,
    "seismic_event_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "prediction_seismic_pkey" PRIMARY KEY ("artifact_id","seismic_event_id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_deformation_class" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "deformation" BOOLEAN NOT NULL DEFAULT true,
    "seismic" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_deformation_class_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_seismic_class" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "vt" BOOLEAN NOT NULL DEFAULT true,
    "lp" BOOLEAN NOT NULL DEFAULT true,
    "tr" BOOLEAN NOT NULL DEFAULT true,
    "tc" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_seismic_class_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_deformation_source" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "source" "ai"."training_deformation_source_type" NOT NULL,
    "latitude" DECIMAL(9,6) NOT NULL,
    "longitude" DECIMAL(9,6) NOT NULL,
    "depth_km" DECIMAL(6,3) NOT NULL,
    "volume_change_m3" DECIMAL(14,2),
    "pressure_change_pa" DECIMAL(14,2),
    "strike_deg" DECIMAL(5,2),
    "dip_deg" DECIMAL(5,2),
    "length_km" DECIMAL(6,3),
    "width_km" DECIMAL(6,3),
    "rake_deg" DECIMAL(5,2),
    "slip_m" DECIMAL(6,3),
    "opening_m" DECIMAL(6,3),
    "poissons_ratio" DECIMAL(4,3) NOT NULL DEFAULT 0.25,
    "shear_modulus_pa" DECIMAL(14,2),
    "los_incidence_deg" DECIMAL(5,2) NOT NULL,
    "los_heading_deg" DECIMAL(6,2) NOT NULL,
    "wavelength_m" DECIMAL(6,4) NOT NULL,
    "noise_model" "ai"."training_noise_model" NOT NULL DEFAULT 'none',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_deformation_source_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_interferogram" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "source" "ai"."training_sample_source" NOT NULL,
    "split" "ai"."training_split" NOT NULL,
    "label" "ai"."training_deformation_label" NOT NULL,
    "frame_id" TEXT,
    "primary_at" DATE,
    "secondary_at" DATE,
    "coherence_mean" DECIMAL(4,3),
    "is_augmented" BOOLEAN NOT NULL DEFAULT false,
    "storage_path" TEXT NOT NULL,
    "deformation_source_id" UUID,
    "volcano_id" UUID,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_interferogram_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_seismic_event" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "source" "ai"."training_sample_source" NOT NULL,
    "split" "ai"."training_split" NOT NULL,
    "label" "ai"."training_seismic_label" NOT NULL,
    "station" TEXT NOT NULL DEFAULT 'LAV',
    "recorded_at" TIMESTAMPTZ(6) NOT NULL,
    "duration_s" DECIMAL(8,3) NOT NULL,
    "sampling_hz" INTEGER NOT NULL,
    "waveform_path" TEXT NOT NULL,
    "spectrogram_path" TEXT,
    "volcano_id" UUID,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_seismic_event_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_seismic" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "nfft" INTEGER NOT NULL,
    "hop" INTEGER NOT NULL,
    "window" "ai"."training_window" NOT NULL,
    "mel_bins" INTEGER NOT NULL,
    "bandpass_low_hz" DECIMAL(5,2) NOT NULL,
    "bandpass_high_hz" DECIMAL(5,2) NOT NULL,
    "class_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_seismic_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_deformation" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "patch_px" INTEGER NOT NULL,
    "wrap_rad" DECIMAL(6,5) NOT NULL,
    "normalize" "ai"."training_normalize" NOT NULL,
    "coherence_min" DECIMAL(4,3) NOT NULL,
    "class_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_deformation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_hyperparameter_pretrain" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "epochs" INTEGER NOT NULL DEFAULT 50,
    "batch_size" INTEGER NOT NULL DEFAULT 32,
    "learning_rate" DOUBLE PRECISION NOT NULL DEFAULT 0.001,
    "optimizer" "ai"."training_optimizer" NOT NULL DEFAULT 'adamw',
    "weight_decay" DECIMAL(10,8) NOT NULL DEFAULT 0.01,
    "lr_schedule" "ai"."training_rate_schedule" NOT NULL DEFAULT 'cosine',
    "seed" INTEGER NOT NULL DEFAULT 42,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_hyperparameter_pretrain_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_target_modules" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "query" BOOLEAN NOT NULL DEFAULT true,
    "key" BOOLEAN NOT NULL DEFAULT false,
    "value" BOOLEAN NOT NULL DEFAULT true,
    "output" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_target_modules_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_hyperparameter_lora" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "rank" INTEGER NOT NULL DEFAULT 8,
    "alpha" INTEGER NOT NULL DEFAULT 16,
    "dropout" DOUBLE PRECISION NOT NULL DEFAULT 0.1,
    "epochs" INTEGER NOT NULL DEFAULT 10,
    "learning_rate" DOUBLE PRECISION NOT NULL DEFAULT 0.0003,
    "target_modules_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_hyperparameter_lora_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_hyperparameter_distill" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "temperature" DOUBLE PRECISION NOT NULL DEFAULT 4.0,
    "alpha" DECIMAL(4,3) NOT NULL DEFAULT 0.7,
    "epochs" INTEGER NOT NULL DEFAULT 30,
    "batch_size" INTEGER NOT NULL DEFAULT 64,
    "learning_rate" DOUBLE PRECISION NOT NULL DEFAULT 0.001,
    "student_architecture" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_hyperparameter_distill_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_hyperparameter_prune" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "target_sparsity" DECIMAL(4,3) NOT NULL DEFAULT 0.7,
    "iterations" INTEGER NOT NULL DEFAULT 5,
    "sparsity_schedule" "ai"."training_sparsity_schedule" NOT NULL DEFAULT 'linear',
    "finetune_epochs_per_iter" INTEGER NOT NULL DEFAULT 3,
    "pruning_criterion" "ai"."training_pruning_criterion" NOT NULL DEFAULT 'l1_magnitude',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_hyperparameter_prune_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_hyperparameter_quantize" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "method" "ai"."training_quantize_method" NOT NULL DEFAULT 'ptq',
    "precision" "ai"."training_precision" NOT NULL DEFAULT 'int8',
    "calibration_samples" INTEGER NOT NULL DEFAULT 100,
    "accuracy_drop_threshold" DECIMAL(6,5) NOT NULL DEFAULT 0.02,
    "qat_epochs" INTEGER NOT NULL DEFAULT 5,
    "qat_learning_rate" DOUBLE PRECISION NOT NULL DEFAULT 0.001,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_hyperparameter_quantize_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_contract" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "signal" "ai"."training_signal" NOT NULL,
    "notes" TEXT,
    "version" INTEGER NOT NULL DEFAULT 1,
    "seismic_id" UUID,
    "deformation_id" UUID,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_contract_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_session" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "signal" "ai"."training_signal" NOT NULL,
    "stage" "ai"."training_stage" NOT NULL,
    "status" "ai"."training_status" NOT NULL,
    "samples" INTEGER NOT NULL,
    "seed" INTEGER NOT NULL,
    "git_sha" TEXT,
    "git_url" TEXT,
    "started_at" TIMESTAMPTZ(6),
    "finished_at" TIMESTAMPTZ(6),
    "error_message" TEXT,
    "hyperparameter_pretrain_id" UUID,
    "hyperparameter_lora_id" UUID,
    "hyperparameter_distill_id" UUID,
    "hyperparameter_prune_id" UUID,
    "hyperparameter_quantize_id" UUID,
    "contract_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_session_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "geo"."volcano" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "gvp_number" INTEGER,
    "name" TEXT NOT NULL,
    "country" TEXT NOT NULL,
    "zone" "geo"."volcano_zone" NOT NULL,
    "latitude" DECIMAL(9,6) NOT NULL,
    "longitude" DECIMAL(9,6) NOT NULL,
    "elevation_m" INTEGER NOT NULL,
    "volcanic_class" TEXT,
    "is_glaciated" BOOLEAN NOT NULL DEFAULT false,
    "is_instrumented" BOOLEAN NOT NULL DEFAULT false,
    "is_held_out" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "volcano_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "geo"."volcano_activity" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "source" "geo"."volcano_activity_source" NOT NULL,
    "started_at" DATE,
    "ended_at" DATE,
    "vei" INTEGER,
    "alert_level" "geo"."volcano_alert_level",
    "is_confirmed" BOOLEAN NOT NULL DEFAULT true,
    "volcano_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "volcano_activity_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "model_artifact_session_id_key" ON "ai"."model_artifact"("session_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_model_artifact_by_promotion" ON "ai"."model_artifact"("tier", "role", "promoted");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_model_artifact_by_registry_slot" ON "ai"."model_artifact"("tier", "role", "created_at" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_model_artifact_by_stage" ON "ai"."model_artifact"("stage");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_model_artifact_by_parent" ON "ai"."model_artifact"("parent_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_model_metric_by_name" ON "ai"."model_metric"("name", "split", "value" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_model_metric_by_artifact" ON "ai"."model_metric"("artifact_id", "created_at" DESC);

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "model_budget_artifact_id_key" ON "ai"."model_budget"("artifact_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_model_budget_by_passed" ON "ai"."model_budget"("passed", "flash_kb");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_prediction_deformation_by_interferogram" ON "ai"."prediction_deformation"("interferogram_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_prediction_deformation_abstained" ON "ai"."prediction_deformation"("artifact_id", "abstained");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_prediction_deformation_recency" ON "ai"."prediction_deformation"("created_at" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_prediction_deformation_by_label" ON "ai"."prediction_deformation"("label", "score" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_prediction_seismic_by_event" ON "ai"."prediction_seismic"("seismic_event_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_prediction_seismic_recency" ON "ai"."prediction_seismic"("created_at" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_prediction_seismic_by_label" ON "ai"."prediction_seismic"("label");

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "training_deformation_class_deformation_seismic_key" ON "ai"."training_deformation_class"("deformation", "seismic");

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "training_seismic_class_vt_lp_tr_tc_key" ON "ai"."training_seismic_class"("vt", "lp", "tr", "tc");

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "training_interferogram_deformation_source_id_key" ON "ai"."training_interferogram"("deformation_source_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_interferogram_by_split" ON "ai"."training_interferogram"("split", "source", "label");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_interferogram_by_coherence_mean" ON "ai"."training_interferogram"("coherence_mean");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_interferogram_by_volcano" ON "ai"."training_interferogram"("volcano_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_seismic_event_by_split" ON "ai"."training_seismic_event"("split", "source", "label");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_seismic_event_by_station" ON "ai"."training_seismic_event"("station", "recorded_at" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_seismic_event_by_volcano" ON "ai"."training_seismic_event"("volcano_id", "recorded_at" DESC);

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "training_target_modules_query_key_value_output_key" ON "ai"."training_target_modules"("query", "key", "value", "output");

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "training_contract_signal_version_key" ON "ai"."training_contract"("signal", "version");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_training_session_by_recency" ON "ai"."training_session"("signal", "created_at" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_training_session_by_stage_and_status" ON "ai"."training_session"("signal", "stage", "status");

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "volcano_gvp_number_key" ON "geo"."volcano"("gvp_number");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_volcano_by_zone" ON "geo"."volcano"("zone");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_volcano_by_position" ON "geo"."volcano"("latitude", "longitude");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_volcano_by_map_viewing" ON "geo"."volcano"("zone", "is_instrumented");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_activity_by_volcano" ON "geo"."volcano_activity"("volcano_id", "started_at" DESC);

-- AddForeignKey
ALTER TABLE "ai"."model_artifact" ADD CONSTRAINT "model_artifact_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "ai"."training_session"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."model_artifact" ADD CONSTRAINT "model_artifact_parent_id_fkey" FOREIGN KEY ("parent_id") REFERENCES "ai"."model_artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."model_metric" ADD CONSTRAINT "model_metric_artifact_id_fkey" FOREIGN KEY ("artifact_id") REFERENCES "ai"."model_artifact"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."model_budget" ADD CONSTRAINT "model_budget_artifact_id_fkey" FOREIGN KEY ("artifact_id") REFERENCES "ai"."model_artifact"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."prediction_deformation" ADD CONSTRAINT "prediction_deformation_artifact_id_fkey" FOREIGN KEY ("artifact_id") REFERENCES "ai"."model_artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."prediction_deformation" ADD CONSTRAINT "prediction_deformation_interferogram_id_fkey" FOREIGN KEY ("interferogram_id") REFERENCES "ai"."training_interferogram"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."prediction_seismic" ADD CONSTRAINT "prediction_seismic_artifact_id_fkey" FOREIGN KEY ("artifact_id") REFERENCES "ai"."model_artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."prediction_seismic" ADD CONSTRAINT "prediction_seismic_seismic_event_id_fkey" FOREIGN KEY ("seismic_event_id") REFERENCES "ai"."training_seismic_event"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_interferogram" ADD CONSTRAINT "training_interferogram_deformation_source_id_fkey" FOREIGN KEY ("deformation_source_id") REFERENCES "ai"."training_deformation_source"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_interferogram" ADD CONSTRAINT "training_interferogram_volcano_id_fkey" FOREIGN KEY ("volcano_id") REFERENCES "geo"."volcano"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_seismic_event" ADD CONSTRAINT "training_seismic_event_volcano_id_fkey" FOREIGN KEY ("volcano_id") REFERENCES "geo"."volcano"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_seismic" ADD CONSTRAINT "training_seismic_class_id_fkey" FOREIGN KEY ("class_id") REFERENCES "ai"."training_seismic_class"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_deformation" ADD CONSTRAINT "training_deformation_class_id_fkey" FOREIGN KEY ("class_id") REFERENCES "ai"."training_deformation_class"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_hyperparameter_lora" ADD CONSTRAINT "training_hyperparameter_lora_target_modules_id_fkey" FOREIGN KEY ("target_modules_id") REFERENCES "ai"."training_target_modules"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_contract" ADD CONSTRAINT "training_contract_seismic_id_fkey" FOREIGN KEY ("seismic_id") REFERENCES "ai"."training_seismic"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_contract" ADD CONSTRAINT "training_contract_deformation_id_fkey" FOREIGN KEY ("deformation_id") REFERENCES "ai"."training_deformation"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_session" ADD CONSTRAINT "training_session_hyperparameter_pretrain_id_fkey" FOREIGN KEY ("hyperparameter_pretrain_id") REFERENCES "ai"."training_hyperparameter_pretrain"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_session" ADD CONSTRAINT "training_session_hyperparameter_lora_id_fkey" FOREIGN KEY ("hyperparameter_lora_id") REFERENCES "ai"."training_hyperparameter_lora"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_session" ADD CONSTRAINT "training_session_hyperparameter_distill_id_fkey" FOREIGN KEY ("hyperparameter_distill_id") REFERENCES "ai"."training_hyperparameter_distill"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_session" ADD CONSTRAINT "training_session_hyperparameter_prune_id_fkey" FOREIGN KEY ("hyperparameter_prune_id") REFERENCES "ai"."training_hyperparameter_prune"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_session" ADD CONSTRAINT "training_session_hyperparameter_quantize_id_fkey" FOREIGN KEY ("hyperparameter_quantize_id") REFERENCES "ai"."training_hyperparameter_quantize"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_session" ADD CONSTRAINT "training_session_contract_id_fkey" FOREIGN KEY ("contract_id") REFERENCES "ai"."training_contract"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "geo"."volcano_activity" ADD CONSTRAINT "volcano_activity_volcano_id_fkey" FOREIGN KEY ("volcano_id") REFERENCES "geo"."volcano"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- (manual) Create Partial Index
-- enforce unique model_artifact per tier and role for promoted
CREATE UNIQUE INDEX IF NOT EXISTS "uq_model_artifact_promoted_slot" ON "ai"."model_artifact" ("tier", "role") WHERE "promoted";

-- (manual) Create Constraint
-- enforce at least one of seismic or deformation relationship per training_contract
ALTER TABLE "ai"."training_contract"
    ADD CONSTRAINT "training_contract_signal_config_check"
    CHECK (
        ("signal" = 'seismic'     AND "seismic_id"     IS NOT NULL AND "deformation_id" IS NULL)
     OR ("signal" = 'deformation' AND "deformation_id" IS NOT NULL AND "seismic_id"     IS NULL)
    );

-- (manual) Create Constraint
-- enforce at least one hyperparameter set per training_session
ALTER TABLE "ai"."training_session"
    ADD CONSTRAINT "training_session_stage_hyperparameter_check"
    CHECK (
        num_nonnulls(hyperparameter_pretrain_id, hyperparameter_lora_id, hyperparameter_distill_id,
                     hyperparameter_prune_id, hyperparameter_quantize_id) = 1
        AND (
            (stage = 'pretrain' AND hyperparameter_pretrain_id IS NOT NULL) OR
            (stage = 'lora'     AND hyperparameter_lora_id     IS NOT NULL) OR
            (stage = 'distill'  AND hyperparameter_distill_id  IS NOT NULL) OR
            (stage = 'prune'    AND hyperparameter_prune_id    IS NOT NULL) OR
            (stage = 'quantize' AND hyperparameter_quantize_id IS NOT NULL)
        )
    );
    