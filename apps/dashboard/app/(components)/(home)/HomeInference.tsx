"use client";

import { useCallback, useEffect, useReducer } from "react";
import { createPortal } from "react-dom";
import Image from "next/image";
import { X } from "lucide-react";
import {
  Button,
  FeedbackThumbs,
  FeedbackThanksIcon,
  Input,
  signalLabel,
} from "@fiery/ui";
import { formatDecimal } from "@fiery/utils";
import { TEST_IDS } from "@/lib/test-ids";
import { IMAGE_LOADING } from "@/lib/constants";
import { useInference } from "@/app/(hooks)/use-inference";
import { useFeedback } from "@/app/(hooks)/use-feedback";
import { usePreview } from "@/app/(hooks)/use-preview";
import { useModalFocus } from "@/app/(hooks)/use-modal-focus";
import {
  inferenceModalView,
  inferenceRequest,
  latestSignalInference,
} from "@/lib/utils";
import { inferenceReducer, inferenceFormInitialState } from "@/lib/reducers";
import {
  TrainingDeformationLabel,
  TrainingSeismicLabel,
  TrainingSignal,
  VolcanoDashboard,
} from "@fiery/types";

type HomeInferenceProps = {
  userId: string;
  volcano: VolcanoDashboard;
  signal: TrainingSignal;
  onClose: () => void;
};

export function HomeInference({
  userId,
  volcano,
  signal,
  onClose,
}: HomeInferenceProps) {
  const close = useCallback(() => onClose(), [onClose]);
  const dialogRef = useModalFocus(true, close);

  const isDeformation = signal === TrainingSignal.deformation;
  const isSeismic = signal === TrainingSignal.seismic;
  const sample = isDeformation
    ? volcano.deformation.sample
    : volcano.seismic.sample;
  const latest = latestSignalInference(volcano, signal);
  const request = inferenceRequest(volcano, signal);
  const previewQuery = usePreview(
    sample
      ? {
          interferogramId: isDeformation ? sample.id : null,
          seismicEventId: isSeismic ? sample.id : null,
        }
      : null,
  );
  const imageSrc = previewQuery.data
    ? `data:${previewQuery.data.contentType};base64,${previewQuery.data.base64}`
    : null;
  const imageAlt = isDeformation
    ? `${volcano.name} interferogram`
    : `${volcano.name} spectrogram`;

  const inferenceMutation = useInference(userId);
  const feedbackMutation = useFeedback(userId);

  const served = inferenceMutation.data?.result ?? null;
  const servedArtifactId = served?.artifact_id ?? null;
  const servedAt = inferenceMutation.submittedAt;

  const [form, dispatch] = useReducer(
    inferenceReducer,
    inferenceFormInitialState,
  );

  useEffect(() => {
    if (!servedArtifactId) return;
    feedbackMutation.reset();
    dispatch({ type: "RESET" });
  }, [servedArtifactId, servedAt]);

  const {
    label,
    score,
    abstained,
    abstainedReason,
    artifactId,
    hasResult,
    submittedAgreed,
    submittedCorrectedDeformation,
    submittedCorrectedSeismic,
    submittedNotes,
    hasSubmitted,
  } = inferenceModalView({
    signal,
    latest,
    served,
    form,
    feedbackSucceeded: feedbackMutation.isSuccess,
  });
  const fieldsDisabled = hasSubmitted || feedbackMutation.isPending;

  const send = (nextAgreed: boolean) => {
    if (!artifactId) return;
    if (
      (isDeformation && submittedCorrectedDeformation == null) ||
      (isSeismic && submittedCorrectedSeismic == null)
    )
      return;
    if (feedbackMutation.isError) feedbackMutation.reset();
    dispatch({ type: "SET_AGREED", agreed: nextAgreed });
    feedbackMutation.mutate({
      agreed: nextAgreed,
      correctedDeformation: isDeformation
        ? submittedCorrectedDeformation
        : null,
      correctedSeismic: isSeismic ? submittedCorrectedSeismic : null,
      note: submittedNotes,
      volcanoId: volcano.id,
      interferogramId: isDeformation ? (sample?.id ?? null) : null,
      seismicEventId: isSeismic ? (sample?.id ?? null) : null,
      artifactId,
    });
  };

  const modal = (
    <>
      <div
        className="fixed inset-0 z-100 bg-black/50"
        onClick={close}
        aria-hidden
      />
      <div
        ref={dialogRef}
        tabIndex={-1}
        className="fixed left-1/2 top-1/2 z-110 w-[min(92vw,28rem)] max-h-[90vh] overflow-y-auto -translate-x-1/2 -translate-y-1/2 rounded-sm border border-white bg-surface-dark p-5 shadow-lg outline-none font-data"
        role="dialog"
        aria-modal
        aria-labelledby="inference-title"
        data-testid={TEST_IDS.inferenceDialog}
      >
        <div className="flex items-center justify-between gap-3">
          <h2
            id="inference-title"
            className="text-base font-semibold text-white"
          >
            {signalLabel[signal]}
          </h2>
          <button
            type="button"
            data-testid={TEST_IDS.inferenceCloseButton}
            onClick={close}
            className="p-1 -mr-1 text-white/70 hover:text-white transition-colors"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-1 text-xs text-white/60 truncate">{volcano.name}</p>
        <div className="mt-4 space-y-3">
          {imageSrc ? (
            <Image
              src={imageSrc}
              alt={imageAlt}
              width={448}
              height={256}
              className="h-40 w-full object-cover rounded-sm border border-white/10"
            />
          ) : (
            <Image
              src={IMAGE_LOADING}
              alt={imageAlt}
              width={448}
              height={256}
              sizes="(max-width: 448px) 92vw, 448px"
              quality={16}
              className="h-40 w-full object-contain rounded-sm border border-white/10"
            />
          )}
          {hasResult ? (
            <div className="space-y-1 text-sm text-white/80">
              {label ? <p>Label: {label}</p> : null}
              {score != null ? <p>Score: {formatDecimal(score)}</p> : null}
              {abstained ? (
                <p>Abstained{abstainedReason ? `: ${abstainedReason}` : ""}</p>
              ) : null}
              {artifactId ? (
                <p className="text-xs text-white/50 break-all">
                  Model {artifactId}
                </p>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-white/50">
              No inference yet for this sample.
            </p>
          )}
          <Button
            data-testid={
              isDeformation
                ? TEST_IDS.inferenceDeformationRunButton
                : TEST_IDS.inferenceSeismicRunButton
            }
            disabled={inferenceMutation.isPending || request == null}
            onClick={() => {
              if (!request) return;
              feedbackMutation.reset();
              inferenceMutation.mutate(request);
            }}
          >
            {inferenceMutation.isPending ? "Inferencing…" : "Run inference"}
          </Button>
          {inferenceMutation.isError ? (
            <p className="text-red-400 text-sm">
              {inferenceMutation.error instanceof Error
                ? inferenceMutation.error.message
                : "Inference request failed."}
            </p>
          ) : null}
          {inferenceMutation.isSuccess ? (
            <p className="text-green-400 text-sm">
              Served inference from model{" "}
              {inferenceMutation.data?.result.artifact_id}.
            </p>
          ) : null}
          {isDeformation ? (
            <select
              aria-label="Corrected deformation label"
              disabled={fieldsDisabled || !artifactId}
              value={submittedCorrectedDeformation ?? ""}
              onChange={(event) => {
                dispatch({
                  type: "SET_CORRECTED_DEFORMATION",
                  label: (event.target.value ||
                    null) as TrainingDeformationLabel | null,
                });
              }}
              className="w-full rounded-md border border-white/10 bg-surface-dark px-3 py-1.5 text-xs text-white"
            >
              <option value="">Select label</option>
              {Object.values(TrainingDeformationLabel).map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          ) : null}
          {isSeismic ? (
            <select
              aria-label="Corrected seismic label"
              disabled={fieldsDisabled || !artifactId}
              value={submittedCorrectedSeismic ?? ""}
              onChange={(event) => {
                dispatch({
                  type: "SET_CORRECTED_SEISMIC",
                  label: (event.target.value ||
                    null) as TrainingSeismicLabel | null,
                });
              }}
              className="w-full rounded-md border border-white/10 bg-surface-dark px-3 py-1.5 text-xs text-white"
            >
              <option value="">Select label</option>
              {Object.values(TrainingSeismicLabel).map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          ) : null}
          <Input
            type="text"
            aria-label="Feedback notes"
            placeholder="Notes"
            disabled={fieldsDisabled || !artifactId}
            value={submittedNotes ?? ""}
            onChange={(event) => {
              dispatch({
                type: "SET_NOTES",
                notes: event.target.value || null,
              });
            }}
          />
          {hasSubmitted ? (
            <FeedbackThanksIcon variant={submittedAgreed ? "up" : "down"} />
          ) : (
            <FeedbackThumbs
              disabled={feedbackMutation.isPending || !artifactId}
              onPositive={() => send(true)}
              onNegative={() => send(false)}
            />
          )}
          {feedbackMutation.isError ? (
            <p className="text-red-400 text-sm">
              {feedbackMutation.error instanceof Error
                ? feedbackMutation.error.message
                : "Feedback request failed."}
            </p>
          ) : null}
        </div>
      </div>
    </>
  );

  return typeof window !== "undefined"
    ? createPortal(modal, document.body)
    : null;
}
