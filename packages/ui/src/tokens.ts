import {
  type ModelTier,
  type ModelRole,
  type ModelMetricName,
  type ModelBudgetMetricName,
  type TrainingSignal,
  type TrainingStatus,
  TrainingStage,
  TrainingSampleSource,
} from "@fiery/types";

export const tierColors: Record<ModelTier, string> = {
  cloud: "border-fiery-white-600 bg-fiery-ash-800/40 text-fiery-white-100",
  edge: "border-amber-400 bg-amber-950/40 text-amber-200",
};

export const tierLabel: Record<ModelTier, string> = {
  cloud: "Cloud",
  edge: "Edge",
};

export const roleColors: Record<ModelRole, string> = {
  screener: "border-green-400 bg-green-950/40 text-green-200",
  teacher: "border-blue-400 bg-blue-950/40 text-blue-200",
  student: "border-red-400 bg-red-950/40 text-red-200",
};

export const roleLabel: Record<ModelRole, string> = {
  screener: "Screener",
  teacher: "Teacher",
  student: "Student",
};

export const signalColors: Record<TrainingSignal, string> = {
  deformation:
    "border-fiery-crimson-400 bg-fiery-crimson-800/40 text-fiery-crimson-200",
  seismic:
    "border-fiery-crimson-400 bg-fiery-crimson-800/40 text-fiery-crimson-300",
};

export const signalLabel: Record<TrainingSignal, string> = {
  deformation: "Ground Deformations",
  seismic: "Seismic Activity",
};

export const metricLabel: Record<ModelMetricName, string> = {
  accuracy: "Acc",
  recall: "Rec",
  precision: "Prec",
  falsePositiveRate: "FPR",
  abstentionRate: "Abs",
  f1Score: "F1",
  macrof1Score: "Macro-F1",
};

export const budgetLabel: Record<ModelBudgetMetricName, string> = {
  flash: "Flash",
  peakRam: "RAM",
  macs: "MACs",
  latency: "Lat",
  energy: "Enrg",
  autonomy: "Auto",
};

export const statusColors: Record<TrainingStatus, string> = {
  pending: "border-zinc-600/50 bg-zinc-950/50 text-zinc-100/80",
  executing: "border-blue-600/50 bg-blue-950/50 text-blue-100/90",
  completed: "border-green-600/50 bg-green-950/50 text-green-100/90",
  failed: "border-red-600/50 bg-red-950/50 text-red-100/90",
  cancelled: "border-amber-600/50 bg-amber-950/50 text-amber-100/90",
};

export const statusLabel: Record<TrainingStatus, string> = {
  pending: "Pending",
  executing: "Running",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

export const sourceValues = [
  TrainingSampleSource.hephaestus,
  TrainingSampleSource.okada,
  TrainingSampleSource.llaima,
  TrainingSampleSource.licsar,
  TrainingSampleSource.villarrica,
] as const;

export const sourceLabel: Record<(typeof sourceValues)[number], string> = {
  hephaestus: "Hephaestus",
  okada: "Okada",
  llaima: "Llaima",
  licsar: "Licsar",
  villarrica: "Villarrica",
};

export const stageValues = [
  TrainingStage.pretrain,
  TrainingStage.lora,
  TrainingStage.distill,
  TrainingStage.prune,
  TrainingStage.quantize,
] as const;

export const stageLabel: Record<(typeof stageValues)[number], string> = {
  pretrain: "Pretrain",
  lora: "LoRA",
  distill: "Distill",
  prune: "Prune",
  quantize: "Quantize",
};
