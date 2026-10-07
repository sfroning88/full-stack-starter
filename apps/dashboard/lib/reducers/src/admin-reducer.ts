import {
  TrainingSignal,
  TrainingStage,
  TrainingSampleSource,
} from "@fiery/types";
import { coerceIngestSource } from "@/lib/utils";

export type AdminPanelState = {
  loadAll: boolean;
  maxSamples: string;
  source: TrainingSampleSource;
  stage: TrainingStage;
  signal: TrainingSignal;
};

export const adminPanelInitialState: AdminPanelState = {
  loadAll: false,
  maxSamples: "",
  source: TrainingSampleSource.hephaestus,
  stage: TrainingStage.lora,
  signal: TrainingSignal.deformation,
};

export type AdminPanelAction =
  | { type: "SET_LOAD_ALL"; loadAll: boolean }
  | { type: "SET_MAX_SAMPLES"; maxSamples: string }
  | { type: "SET_SOURCE"; source: TrainingSampleSource }
  | { type: "SET_STAGE"; stage: TrainingStage }
  | { type: "SET_SIGNAL"; signal: TrainingSignal }
  | { type: "RESET" };

export function adminReducer(
  state: AdminPanelState,
  action: AdminPanelAction,
): AdminPanelState {
  switch (action.type) {
    case "SET_LOAD_ALL":
      return { ...state, loadAll: action.loadAll };
    case "SET_MAX_SAMPLES":
      return { ...state, maxSamples: action.maxSamples };
    case "SET_SOURCE":
      return { ...state, source: coerceIngestSource(action.source) };
    case "SET_STAGE":
      return { ...state, stage: action.stage };
    case "SET_SIGNAL":
      return { ...state, signal: action.signal };
    case "RESET":
      return adminPanelInitialState;
  }
}
