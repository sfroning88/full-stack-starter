-- AlterTable
ALTER TABLE "ai"."training_seismic" ADD COLUMN     "normalize" "ai"."training_normalize" NOT NULL,
ADD COLUMN     "sampling_hz" INTEGER NOT NULL,
ADD COLUMN     "snr_min" DECIMAL(6,3) NOT NULL,
ADD COLUMN     "window_s" DECIMAL(8,3) NOT NULL;
