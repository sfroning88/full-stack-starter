import type {
  TrainingDeformationLabel,
  TrainingSeismicLabel,
} from "@fiery/types";

type InferenceFormState = {
  agreed: boolean | null;
  correctedDeformation: TrainingDeformationLabel | null;
  correctedSeismic: TrainingSeismicLabel | null;
  notes: string | null;
};

export const inferenceFormInitialState: InferenceFormState = {
  agreed: null,
  correctedDeformation: null,
  correctedSeismic: null,
  notes: null,
};

type InferenceFormAction =
  | { type: "SET_AGREED"; agreed: boolean }
  | {
      type: "SET_CORRECTED_DEFORMATION";
      label: TrainingDeformationLabel | null;
    }
  | { type: "SET_CORRECTED_SEISMIC"; label: TrainingSeismicLabel | null }
  | { type: "SET_NOTES"; notes: string | null }
  | { type: "RESET" };

export function inferenceReducer(
  state: InferenceFormState,
  action: InferenceFormAction,
): InferenceFormState {
  switch (action.type) {
    case "SET_AGREED":
      return { ...state, agreed: action.agreed };
    case "SET_CORRECTED_DEFORMATION":
      return { ...state, correctedDeformation: action.label };
    case "SET_CORRECTED_SEISMIC":
      return { ...state, correctedSeismic: action.label };
    case "SET_NOTES":
      return { ...state, notes: action.notes };
    case "RESET":
      return inferenceFormInitialState;
  }
}
