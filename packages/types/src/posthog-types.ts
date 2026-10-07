export const POSTHOG_EVENTS = {
  cookie_banner_dismissed: "cookie_banner_dismissed",
  privacy_policy_opened: "privacy_policy_opened",
  privacy_policy_closed: "privacy_policy_closed",
  ingest: "ingest_requested",
  refine: "refine_requested",
  train: "train_requested",
  inference: "inference_requested",
  feedback: "feedback_given",
  batch: "batch_requested",
  promote: "promote_requested",
  refresh: "refresh_requested",
} as const;
