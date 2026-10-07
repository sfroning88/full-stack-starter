import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  LabelHTMLAttributes,
  ReactNode,
} from "react";
import { TrainingSignal, TrainingStage } from "@fiery/types";
import { ThumbsDown, ThumbsUp } from "iconoir-react";
import { iconClass, btnClass, selectClass, onSelectChange } from "./dynamics";
import {
  signalLabel,
  sourceValues,
  sourceLabel,
  stageValues,
  stageLabel,
} from "./tokens";

export function Dot({ className }: { className?: string }) {
  return (
    <span className={`select-none ${className ?? "text-crimson/25"}`}>·</span>
  );
}

export function Badge({
  children,
  colorScheme = "dark",
}: {
  children: ReactNode;
  colorScheme: "dark" | "light";
}) {
  if (colorScheme === "light") {
    return (
      <span className="inline-flex items-center rounded-sm border border-black/15 px-1.5 md:px-2 py-0.5 text-[10px] md:text-xs text-crimson/50 font-data-mono whitespace-nowrap">
        {children}
      </span>
    );
  } else {
    return (
      <span className="inline-flex items-center rounded-sm border border-white/15 px-1.5 md:px-2 py-0.5 text-[10px] md:text-xs text-white/50 font-data-mono whitespace-nowrap">
        {children}
      </span>
    );
  }
}

export function Button({
  children,
  className,
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-md border border-white font-data font-semibold transition-colors px-3 py-1.5 text-xs md:px-4 md:py-2 md:text-sm bg-white/4 text-white hover:bg-white/12 disabled:border-white/40 disabled:bg-white/2 disabled:text-white/50 disabled:cursor-not-allowed disabled:hover:bg-white/2 ${className ?? ""}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function Input({
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`block rounded-md border border-white bg-white/4 font-data font-semibold text-white placeholder:text-white/50 px-3 py-1.5 text-xs md:px-4 md:py-2 md:text-sm read-only:opacity-60 disabled:opacity-60 ${className ?? ""}`}
      {...props}
    />
  );
}

export function Label({
  children,
  className,
  ...props
}: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={`block text-sm font-semibold text-white ${className ?? ""}`}
      {...props}
    >
      {children}
    </label>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h3 className="text-[10px] md:text-[11px] font-semibold uppercase tracking-[0.15em] text-white/40">
      {children}
    </h3>
  );
}

export function FeedbackThumbs({
  onPositive,
  onNegative,
  disabled,
  className,
}: {
  onPositive: () => void;
  onNegative: () => void;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <div
      className={`inline-flex items-center gap-1.5 ${className ?? ""}`}
      role="group"
      aria-label="Prediction feedback"
    >
      <button
        type="button"
        disabled={disabled}
        onClick={onPositive}
        className={btnClass}
        aria-label="Mark prediction as helpful"
      >
        <ThumbsUp className={iconClass} strokeWidth={2} />
      </button>
      <button
        type="button"
        disabled={disabled}
        onClick={onNegative}
        className={btnClass}
        aria-label="Mark prediction as not helpful"
      >
        <ThumbsDown className={iconClass} strokeWidth={2} />
      </button>
    </div>
  );
}

export function FeedbackThanksIcon({
  variant,
  className,
}: {
  variant: "up" | "down";
  className?: string;
}) {
  const Icon = variant === "up" ? ThumbsUp : ThumbsDown;
  return (
    <Icon
      className={`${iconClass} shrink-0 text-fiery-crimson-400 ${className ?? ""}`}
      strokeWidth={2}
    />
  );
}

export function SignalDropdown({
  value,
  onChange,
  className,
  testId,
}: {
  value: TrainingSignal;
  onChange: (value: TrainingSignal) => void;
  className?: string;
  testId?: string;
}) {
  return (
    <select
      aria-label="Signal"
      data-testid={testId}
      value={value}
      onChange={onSelectChange(onChange)}
      className={`${selectClass} ${className ?? ""}`}
    >
      {([TrainingSignal.deformation, TrainingSignal.seismic] as const).map(
        (signal) => (
          <option key={signal} value={signal}>
            {signalLabel[signal]}
          </option>
        ),
      )}
    </select>
  );
}

export function SourceDropdown({
  value,
  onChange,
  className,
  testId,
}: {
  value: (typeof sourceValues)[number];
  onChange: (value: (typeof sourceValues)[number]) => void;
  className?: string;
  testId?: string;
}) {
  return (
    <select
      aria-label="Source"
      data-testid={testId}
      value={value}
      onChange={onSelectChange(onChange)}
      className={`${selectClass} ${className ?? ""}`}
    >
      {sourceValues.map((source) => (
        <option key={source} value={source}>
          {sourceLabel[source]}
        </option>
      ))}
    </select>
  );
}

export function StageDropdown({
  value,
  onChange,
  className,
  testId,
}: {
  value: TrainingStage;
  onChange: (value: TrainingStage) => void;
  className?: string;
  testId?: string;
}) {
  return (
    <select
      aria-label="Stage"
      data-testid={testId}
      value={value}
      onChange={onSelectChange(onChange)}
      className={`${selectClass} ${className ?? ""}`}
    >
      {stageValues.map((stage) => (
        <option key={stage} value={stage}>
          {stageLabel[stage]}
        </option>
      ))}
    </select>
  );
}
